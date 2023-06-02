import json
import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from dateutil.relativedelta import relativedelta

from extensions.module_result.models.primitives import (
    OxygenSaturation,
)
from extensions.module_result.modules.visualizer import HTMLVisualizer
from sdk.common.utils.common_functions_utils import round_half_up
from sdk.common.utils.validators import utc_str_field_to_val, remove_none_values
from ._utils import build_deviation_dict


@dataclass
class Field:
    title: str
    value: Optional[str]


class OxygenSaturationVisualizer(HTMLVisualizer):
    TITLE = "Oxygen Saturation"
    MAXIMUM_VALUE = 100
    MINIMUM_VALUE = 70
    template_name = "oxygen_saturation.html"

    def get_context(self) -> dict:
        config = self.module.find_config(self.deployment.moduleConfigs, None)
        if not config:
            return {}

        with self.module.configure(config):
            primitives: list[OxygenSaturation] = self._fetch_primitives()  # noqa
            if not primitives:
                return {}

        rag = [item.to_dict() for item in config.ragThresholds or []]

        for primitive in primitives:
            primitive.value = primitive.value * 100

        weekly_data = self._build_big_chart_view(primitives, rag)
        last_week_data = self._build_small_chart_view(primitives, rag)
        min_item, max_item = self._extract_min_max_values(primitives)
        return {
            "title": config.moduleName or self.TITLE,
            "unit": primitives[0].valueUnit,
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

    def model_to_view(self, primitive: OxygenSaturation) -> dict:
        return {
            "date": utc_str_field_to_val(primitive.startDateTime),
            OxygenSaturation.VALUE: primitive.value,
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

            deviation_data_view.append(
                {
                    "day": day,
                    **build_deviation_dict(
                        scores, self.MINIMUM_VALUE, self.MAXIMUM_VALUE
                    ),
                }
            )

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

    def _get_median_field(self, primitives: list[OxygenSaturation]):
        median = self._calculate_median(primitives)
        return Field(
            '6 month median<span class="superscripts">*<span>2</span></span>',
            f"{median}" f"{primitives[0].valueUnit}",
        )

    @staticmethod
    def _extract_min_max_values(
        primitives: list[OxygenSaturation],
    ) -> (OxygenSaturation, OxygenSaturation):
        min_item = min(
            primitives,
            key=lambda p: (p.value, -p.startDateTime.timestamp()),
        )
        max_item = max(primitives, key=lambda p: (p.value, p.startDateTime.timestamp()))
        return min_item, max_item

    def _calculate_mean_with_deviation(
        self,
        items: list[OxygenSaturation],
        date: Optional[datetime],
        date_field_name="day",
    ) -> dict[str, Union[float, datetime]]:
        """Calculate a median value from primitives"""
        if not items:
            if date:
                return {date_field_name: date}
            return {}

        scores = [x.value for x in items]
        mean = statistics.mean(scores)
        result = {OxygenSaturation.VALUE: round_half_up(mean, 1), date_field_name: date}
        if len(scores) >= 2:
            result.update(
                build_deviation_dict(scores, self.MINIMUM_VALUE, self.MAXIMUM_VALUE)
            )

        return remove_none_values(result)

    @staticmethod
    def _calculate_median(items: list[OxygenSaturation]):
        return round_half_up(statistics.median([x.value for x in items]), 1)

    @staticmethod
    def _get_date_range_str(start, end) -> str:
        return f"{start.strftime('%d %b')} - {end.strftime('%d %b')}"

    @staticmethod
    def _to_str(oxygen_saturation: OxygenSaturation) -> str:
        return (
            f"{round_half_up(oxygen_saturation.value)}"
            f"{oxygen_saturation.valueUnit} "
            f"({oxygen_saturation.startDateTime.strftime('%d %b')})"
        )
