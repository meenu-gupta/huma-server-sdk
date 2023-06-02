import json
import statistics
from collections import OrderedDict
from datetime import datetime
from typing import Optional, Union

from dateutil import rrule
from dateutil.relativedelta import relativedelta

from extensions.common.sort import SortField
from extensions.module_result.models.primitives import Primitives, BodyMeasurement
from extensions.module_result.models.primitives.primitive import HumaMeasureUnit
from extensions.module_result.modules.visualizer import HTMLVisualizer
from extensions.module_result.modules.visualizer._utils import (
    build_deviation_dict,
    get_date_range_str,
)
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from sdk.common.utils.common_functions_utils import round_half_up
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values, utc_str_field_to_val


class BodyMeasurementHTMLVisualizer(HTMLVisualizer):
    TITLE = "Body Measurements"
    template_name = "body_measurement.html"

    FIELD_NAMES = [
        BodyMeasurement.WAIST_CIRCUMFERENCE,
        BodyMeasurement.HIP_CIRCUMFERENCE,
        BodyMeasurement.TOTAL_BODY_FAT,
        BodyMeasurement.VISCERAL_FAT,
        BodyMeasurement.WAIST_TO_HIP_RATIO,
    ]
    FIELD_TITLES = [
        "Waist circumference",
        "Hip circumference",
        "Total body fat",
        "Visceral fat",
        "Waist-to-hip ratio",
    ]
    FIELD_UNITS = [
        f" {HumaMeasureUnit.WAIST_CIRCUMFERENCE.value}",
        f" {HumaMeasureUnit.HIP_CIRCUMFERENCE.value}",
        "%",
        " litres",
        "",
    ]
    MAX_VALUES = [500, 500, -10000, -10000, 1]
    ROUND_DECIMALS = [1, 1, 1, 1, 2]
    DEFAULT_VALUES = [None, None, 0, 0, None]

    def get_context(self) -> dict:
        config = self.module.find_config(self.deployment.moduleConfigs, None)
        if not config:
            return {}

        with self.module.configure(config):
            primitives: list[BodyMeasurement] = self._fetch_primitives()  # noqa
            if not primitives:
                return {}

        each_primitives = [[], [], [], [], []]
        for ind, field_name in enumerate(self.FIELD_NAMES):
            default_value = self.DEFAULT_VALUES[ind]
            each_primitives[ind] = [
                p
                for p in primitives
                if p.get_field_value(field_name, default_value) != default_value
            ]

        weekly_data = self._build_big_chart_view(each_primitives)
        small_chart_view = self._build_small_chart_view(each_primitives)
        min_max_items = self._extract_min_max_values(each_primitives)
        data = []
        title = config.moduleName or self.TITLE
        for ind, val in enumerate(self.FIELD_NAMES):
            count = len(each_primitives[ind])
            each_data = {
                "weekly_data": json.dumps(weekly_data[ind]),
                "last_week_data": json.dumps(small_chart_view[ind]),
                "isShow": json.dumps(count > 0),
            }
            if count:
                min_value = min_max_items[ind]["min_item"].get_field_value(val)
                max_value = min_max_items[ind]["max_item"].get_field_value(val)
                min_value = round_half_up(min_value, self.ROUND_DECIMALS[ind])
                max_value = round_half_up(max_value, self.ROUND_DECIMALS[ind])
                field_unit = self.FIELD_UNITS[ind]
                each_data.update(
                    {
                        "title": title,
                        "subtitle": self.FIELD_TITLES[ind],
                        "unit": self.FIELD_UNITS[ind].strip(),
                        "fields": [
                            {
                                "title": "Total number of data points",
                                "value": str(count),
                            },
                            self._get_median_field(
                                each_primitives[ind],
                                val,
                                self.ROUND_DECIMALS[ind],
                                field_unit,
                            ),
                            {
                                "title": "MIN",
                                "value": f"{min_value}{field_unit} ({min_max_items[ind]['min_item'].startDateTime.strftime('%d %b')})",
                            },
                            {
                                "title": "MAX",
                                "value": f"{max_value}{field_unit} ({min_max_items[ind]['max_item'].startDateTime.strftime('%d %b')})",
                            },
                        ],
                        "max_value": self.MAX_VALUES[ind],
                    }
                )
            data.append(each_data)

        return {"data": data}

    def _build_big_chart_view(self, primitives) -> list:
        date_range = get_date_range_str(self.start_date_time, self.end_date_time)
        chart_view = []
        for ind, field_name in enumerate(self.FIELD_NAMES):
            weekly_data = self._build_weekly_view(
                primitives[ind], self.start_date_time, self.end_date_time
            )
            each_weekly_data = [
                self._calculate_mean_with_deviation(
                    items, date, field_name, self.ROUND_DECIMALS[ind], "month"
                )
                for date, items in weekly_data.items()
            ]
            chart_view.append({"dateRange": date_range, "data": each_weekly_data})

        return chart_view

    def _build_small_chart_view(self, primitives) -> list:
        last_week_data_view = []
        for ind, field_name in enumerate(self.FIELD_NAMES):
            if not primitives[ind]:
                last_week_data_view.append({})
                continue

            last_primitive_date = primitives[ind][-1].startDateTime
            week_ago = last_primitive_date - relativedelta(weeks=1)
            last_week = self._slice_data_by_date(
                primitives[ind],
                start=week_ago,
                end=last_primitive_date,
                field_name=field_name,
            )

            (
                last_week_data,
                deviation_data_view,
            ) = self._calculate_scores(last_week)

            last_week_data_view.append(
                {
                    "dateRange": get_date_range_str(
                        self._get_first_day(last_week_data), last_primitive_date
                    ),
                    "data": last_week_data,
                    "deviationData": deviation_data_view,
                }
            )

        return last_week_data_view

    def _calculate_scores(self, last_week_data):
        deviation_data_view = []
        for day, values in last_week_data.items():
            scores = [v["value"] for v in values]
            if len(scores) < 2:
                deviation_data_view.append({"day": day})
                continue

            deviation_data_view.append({"day": day, **build_deviation_dict(scores)})
        for key, values in last_week_data.items():
            if len(values) > 3:
                values[:] = values[:3]
        last_week_data = self._grouped_data_to_array(last_week_data)
        return last_week_data, deviation_data_view

    def _slice_data_by_date(
        self, primitives: list[BodyMeasurement], start, end, field_name=None
    ) -> OrderedDict:
        frmt = "%Y-%m-%d"
        dates = rrule.rrule(freq=rrule.DAILY, dtstart=start, until=end)
        daily_data = OrderedDict((date.strftime(frmt), []) for date in dates[1:])
        for primitive in primitives[::-1]:
            if primitive.startDateTime < start:
                break

            day_str = primitive.startDateTime.strftime(frmt)
            if day_str not in daily_data:
                continue

            daily_data[day_str].append(
                self._questionnaire_to_view(primitive, field_name)
            )

        for day, data in daily_data.items():
            if not data:
                continue
            values_for_the_day = [item["value"] for item in data]
            mean = statistics.mean(values_for_the_day)
            for item in data:
                item["middleDayValue"] = mean
        return daily_data

    def _get_median_field(
        self,
        primitives: list[BodyMeasurement],
        field_name: str,
        round_decimals: int,
        unit: str,
    ):
        median = self._calculate_median(primitives, field_name, round_decimals)
        return {
            "title": '6 month median<span class="superscripts">*<span>2</span></span>',
            "value": f"{median}{unit}",
        }

    @staticmethod
    def _calculate_median(
        items: list[BodyMeasurement], field_name: str, round_decimals: int
    ):
        median = statistics.median([x.get_field_value(field_name) for x in items])
        return round_half_up(median, round_decimals)

    def _extract_min_max_values(self, primitives: list) -> list:
        values = []
        for ind, field_name in enumerate(self.FIELD_NAMES):
            if not primitives[ind]:
                values.append({"min_item": None, "max_item": None})
                continue

            min_item = min(
                primitives[ind],
                key=lambda p: (
                    p.get_field_value(field_name, int(10e6)),
                    -p.startDateTime.timestamp(),
                ),
            )
            max_item = max(
                primitives[ind],
                key=lambda p: (
                    p.get_field_value(field_name, int(-10e6)),
                    p.startDateTime.timestamp(),
                ),
            )

            values.append({"min_item": min_item, "max_item": max_item})
        return values

    @autoparams("repo")
    def _fetch_primitives(self, repo: ModuleResultRepository) -> Primitives:
        primitives = repo.retrieve_primitives(
            user_id=self.user.id,
            module_id=self.module.moduleId,
            primitive_name=BodyMeasurement.__name__,
            skip=0,
            limit=int(10e6),
            direction=SortField.Direction.ASC,
            from_date_time=self.start_date_time,
            to_date_time=self.end_date_time,
            module_config_id=self.module.config.id,
        )
        self._apply_timezone_to_primitives(primitives)
        return primitives

    @staticmethod
    def _calculate_mean_with_deviation(
        items: list[BodyMeasurement],
        date: Optional[datetime],
        field_name: str,
        round_decimals: int,
        date_field_name="day",
    ) -> dict[str, Union[float, datetime]]:
        """Calculate a median value from primitives"""
        if not items:
            if date:
                return {date_field_name: date}
            return {}

        scores = [x.get_field_value(field_name) for x in items]
        mean = round_half_up(statistics.mean(scores), round_decimals)
        result = {"value": mean, date_field_name: date}
        if len(scores) >= 2:
            result.update(build_deviation_dict(scores))

        return remove_none_values(result)

    @staticmethod
    def _questionnaire_to_view(primitive: BodyMeasurement, field_name: str) -> dict:
        return {
            "date": utc_str_field_to_val(primitive.startDateTime),
            "value": primitive.get_field_value(field_name),
        }
