import statistics
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional

import pytz
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from jinja2 import Environment, PackageLoader
from pytz.tzinfo import BaseTzInfo

from extensions.authorization.models.user import User
from extensions.common.sort import SortField
from extensions.deployment.models.deployment import Deployment
from extensions.module_result.models.primitives import Primitives, Primitive
from extensions.module_result.modules.module import Module
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from sdk.common.utils.common_functions_utils import (
    find_last_less_or_equal_element_index,
    round_half_up,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import (
    utc_str_val_to_field,
    utc_str_to_date,
    utc_str_field_to_val,
)

date_frmt = "%Y-%m-%d"


@dataclass
class Field:
    title: str
    value: Optional[str]


class HTMLVisualizer(ABC):
    template_name: str = None
    jinja_env: Environment = Environment(
        loader=PackageLoader("extensions.module_result.modules.visualizer")
    )
    full_height = False

    def __init__(
        self,
        module: Optional[Module],
        user: User,
        deployment: Deployment,
        start_date_time: datetime,
        end_date_time: datetime,
    ):
        self.module = module
        self.user = user
        self.deployment = deployment
        self.timezone = pytz.timezone(user.timezone or "UTC")
        if start_date_time.tzinfo is None:
            start_date_time = start_date_time.replace(tzinfo=pytz.UTC)
        if end_date_time.tzinfo is None:
            end_date_time = end_date_time.replace(tzinfo=pytz.UTC)

        start_date_time = start_date_time.astimezone(self.timezone)
        self.start_date_time = datetime.combine(
            start_date_time, time(), start_date_time.tzinfo
        )
        self.end_date_time = end_date_time.astimezone(self.timezone)

    @abstractmethod
    def get_context(self) -> dict:
        raise NotImplementedError

    def model_to_view(self, primitive: Primitive) -> dict:
        raise NotImplementedError

    def render_html(self) -> str:
        context = self.get_context()
        template = self.jinja_env.get_template(self.template_name)
        return template.render(**context)

    def _build_weekly_view(
        self,
        primitives: Primitives,
        start: datetime,
        end: datetime,
    ) -> dict:
        """
        Builds an ordered dict of primitives,
        grouped by their primitive.startDateTime week start date.
        Example of result:
        {
          "2021-10-01": [],
          "2021-10-08": [Primitive1, Primitive2],
          "2021-10-15": [Primitive3],
          "2021-10-22": []
        }
        """
        weeks_dates = self._build_weeks_array(start, end, self.timezone)
        weekly_data = OrderedDict((d.strftime(date_frmt), []) for d in weeks_dates)
        dates_iterator = iter(weeks_dates)
        start_of_week = next(dates_iterator, None)
        end_of_week = next(dates_iterator, None)
        primitives.sort(key=lambda p: p.startDateTime)
        for primitive in primitives:
            while end_of_week and primitive.startDateTime >= end_of_week:
                start_of_week = end_of_week
                end_of_week = next(dates_iterator, None)

            weekly_data[start_of_week.strftime(date_frmt)].append(primitive)

        return weekly_data

    @staticmethod
    def _build_weeks_array(
        start: datetime, end: datetime, timezone: BaseTzInfo
    ) -> list[datetime]:
        days = [1, 8, 15, 22]
        next_month_start = start.replace(day=1) + relativedelta(months=1)
        dates = rrule.rrule(freq=rrule.MONTHLY, dtstart=next_month_start, until=end)
        dates = [start, *dates]
        correct_dates = []
        for date_i, date in enumerate(dates):
            date = timezone.normalize(date).replace(hour=0)
            start_i = find_last_less_or_equal_element_index(date.day, days)
            for d in days[start_i:]:
                new_date = date.replace(day=d)
                if new_date <= end:
                    correct_dates.append(new_date)

        return correct_dates

    def _slice_data_by_date(self, primitives: Primitives, start, end) -> OrderedDict:
        dates = rrule.rrule(freq=rrule.DAILY, dtstart=start, until=end)
        daily_data = OrderedDict((date.strftime(date_frmt), []) for date in dates[1:])
        for primitive in primitives[::-1]:
            if primitive.startDateTime < start:
                break

            day_str = primitive.startDateTime.strftime(date_frmt)
            if day_str not in daily_data:
                continue

            daily_data[day_str].append(primitive)

        for day, data in daily_data.items():
            if not data:
                continue

            data.sort(key=lambda p: p.startDateTime)
            data[:] = [self.model_to_view(p) for p in data]
            values_for_the_day = [item["value"] for item in data]
            mean = statistics.mean(values_for_the_day)
            for item in data:
                item["middleDayValue"] = round_half_up(mean, 1)

        return daily_data

    @staticmethod
    def _get_first_day(data: list[dict], field_name: str = "date"):
        """Extracts start date or datetime string of the first record in the list and converts it to datetime"""
        week_start_date_str = data[0][field_name]
        try:
            start = utc_str_val_to_field(week_start_date_str)
        except ConvertibleClassValidationError:
            start = utc_str_to_date(week_start_date_str)
        return start

    @autoparams("repo")
    def _fetch_primitives(self, repo: ModuleResultRepository) -> Primitives:
        primitives = repo.retrieve_primitives(
            user_id=self.user.id,
            module_id=self.module.moduleId,
            primitive_name=self.module.primitives[0].__name__,
            skip=0,
            limit=int(10e6),
            direction=SortField.Direction.ASC,
            from_date_time=self.start_date_time,
            to_date_time=self.end_date_time,
            module_config_id=self.module.config.id,
        )
        self._apply_timezone_to_primitives(primitives)
        return primitives

    def _apply_timezone_to_primitives(self, primitives: Primitives) -> None:
        for primitive in primitives:
            if primitive.startDateTime.tzinfo is None:
                primitive.startDateTime = primitive.startDateTime.replace(
                    tzinfo=pytz.UTC
                )
            primitive.startDateTime = primitive.startDateTime.astimezone(self.timezone)
            if not primitive.endDateTime:
                continue
            if primitive.endDateTime.tzinfo is None:
                primitive.endDateTime = primitive.endDateTime.replace(tzinfo=pytz.UTC)
            primitive.endDateTime = primitive.endDateTime.astimezone(self.timezone)

    @staticmethod
    def _grouped_data_to_array(grouped_data: OrderedDict):
        result = []
        for day, values in grouped_data.items():
            if values:
                result.extend(values)
            else:
                day = datetime.strptime(day, date_frmt).replace(hour=1)
                result.append({"date": utc_str_field_to_val(day)})

        return result
