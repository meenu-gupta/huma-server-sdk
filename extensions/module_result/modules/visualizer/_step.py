import json
import statistics
from datetime import datetime
from typing import Optional, Union

from dateutil.relativedelta import relativedelta

from extensions.module_result.models.primitives import (
    Step,
)
from extensions.module_result.modules.visualizer import Field, HTMLVisualizer
from sdk.common.utils.common_functions_utils import round_half_up
from sdk.common.utils.validators import utc_str_field_to_val, remove_none_values
from ._utils import build_deviation_dict


class StepHTMLVisualizer(HTMLVisualizer):
    TITLE = "Steps"
    MINIMUM_VALUE = 0
    template_name = "steps.html"

    def get_context(self) -> dict:
        config = self.module.find_config(self.deployment.moduleConfigs, None)
        if not config:
            return {}

        with self.module.configure(config):
            primitives: list[Step] = self._fetch_primitives()  # noqa
            if not primitives:
                return {}

        rag = [item.to_dict() for item in config.ragThresholds or []]

        weekly_data = self._build_big_chart_view(primitives, rag)
        last_week_data = self._build_small_chart_view(primitives, rag)
        min_item, max_item = self._extract_min_max_values(primitives)

        return {
            "title": config.moduleName or self.TITLE,
            "fields": [
                Field("Total number of data points", str(len(primitives))),
                self._get_median_field(primitives),
                Field("MIN", self._to_str(min_item)),
                Field("MAX", self._to_str(max_item)),
            ],
            "min_item": min_item,
            "max_item": max_item,
            "weekly_data": json.dumps(weekly_data),
            "last_week_data": json.dumps(last_week_data),
        }

    def _build_big_chart_view(self, primitives, rag):
        weekly_data = self._build_weekly_view(
            primitives, self.start_date_time, self.end_date_time
        )
        weekly_data_view = [
            self._calculate_mean_with_deviation(items, date, "month")
            for date, items in weekly_data.items()
        ]
        return {
            "ragThresholds": rag,
            "dateRange": self._get_date_range_str(
                self.start_date_time, self.end_date_time
            ),
            "data": weekly_data_view,
        }

    def _build_small_chart_view(self, primitives, rag):
        last_primitive_date = primitives[-1].startDateTime
        week_ago = last_primitive_date - relativedelta(weeks=1)
        last_week_data = self._slice_data_by_date(
            primitives, start=week_ago, end=last_primitive_date
        )
        deviation_data_view = []
        for day, values in last_week_data.items():
            scores = [v["value"] for v in values]
            if len(scores) < 2:
                deviation_data_view.append({"day": day})
                continue

            deviation_data_view.append({"day": day, **build_deviation_dict(scores)})
        for key, values in last_week_data.items():
            if len(values) > 3:
                values[:] = values[-3:]
        last_week_data = self._grouped_data_to_array(last_week_data)
        return {
            "ragThresholds": rag,
            "dateRange": self._get_date_range_str(
                self._get_first_day(last_week_data), last_primitive_date
            ),
            "data": last_week_data,
            "deviationData": deviation_data_view,
        }

    def _get_median_field(self, primitives: list[Step]):
        median = self._calculate_median(primitives)
        return Field(
            '6 month median<span class="superscripts">*<span>2</span></span>',
            f"{median}",
        )

    @staticmethod
    def _extract_min_max_values(
        primitives: list[Step],
    ) -> (Step, Step):
        min_item = min(
            primitives,
            key=lambda p: (p.value, -p.startDateTime.timestamp()),
        )
        max_item = max(primitives, key=lambda p: (p.value, p.startDateTime.timestamp()))
        return min_item, max_item

    @staticmethod
    def _calculate_mean_with_deviation(
        items: list[Step], date: Optional[datetime], date_field_name="day"
    ) -> dict[str, Union[float, datetime]]:
        """
        Calculate a median value from primitives
        """
        if not items:
            if date:
                return {date_field_name: date}
            return {}

        scores = [x.value for x in items]
        mean = statistics.mean(scores)
        result = {Step.VALUE: round_half_up(mean), date_field_name: date}
        if len(scores) >= 2:
            result.update(build_deviation_dict(scores))

        return remove_none_values(result)

    @staticmethod
    def _calculate_median(items: list[Step]):
        return round_half_up(statistics.median([x.value for x in items]))

    @staticmethod
    def _get_date_range_str(start, end) -> str:
        return f"{start.strftime('%d %b')} - {end.strftime('%d %b')}"

    def model_to_view(self, primitive: Step) -> dict:
        return {
            "date": utc_str_field_to_val(primitive.startDateTime),
            Step.VALUE: primitive.value,
        }

    @staticmethod
    def _to_str(step: Step) -> str:
        return f"{step.value} " f"({step.startDateTime.strftime('%d %b')})"
