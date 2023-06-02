import json
import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from dateutil.relativedelta import relativedelta

from extensions.module_result.models.module_config import RagThreshold
from extensions.module_result.models.primitives import BloodGlucose
from extensions.module_result.models.primitives.primitive import MeasureUnit
from extensions.module_result.modules.visualizer import HTMLVisualizer, date_frmt
from sdk.common.utils.common_functions_utils import round_half_up
from sdk.common.utils.validators import utc_str_field_to_val, remove_none_values
from ._utils import build_deviation_dict, get_date_range_str


@dataclass
class Field:
    title: str
    value: Optional[str]


class BloodGlucoseVisualizer(HTMLVisualizer):
    TITLE = "Blood Glucose"
    template_name = "blood_glucose.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = self.module.find_config(self.deployment.moduleConfigs, None)
        self.module.config = config
        self.min = 0
        self.max = 26
        self.units = self._get_custom_units()
        if self.units and self.units is not MeasureUnit.MILLIMOLES_PER_LITRE:
            convert = BloodGlucose.UNITS_CONVERTERS_MAP.get(self.units)
            if convert:
                self.max = convert(self.max)

    def _get_custom_units(self) -> MeasureUnit:
        units = MeasureUnit.MILLIMOLES_PER_LITRE
        if self.module.config.customUnit:
            units = MeasureUnit(self.module.config.customUnit)
        if user_units := self.user.get_preferred_units_for_module(self.module.moduleId):
            units = MeasureUnit(user_units)
        return units

    def get_context(self) -> dict:
        config = self.module.config
        primitives: list[BloodGlucose] = self._fetch_primitives()  # noqa
        if not primitives:
            return {}

        rag = self._build_rag(config.ragThresholds or [], self.units)
        weekly_data = self._build_big_chart_view(primitives, rag)
        last_week_data = self._build_small_chart_view(primitives, rag)
        min_item, max_item = self._extract_min_max_values(primitives)
        return {
            "title": config.moduleName or self.TITLE,
            "unit": self.units.value,
            "fields": [
                Field("Total number of data points", str(len(primitives))),
                self._get_median_field(primitives),
                Field("MIN", self._to_str(min_item)),
                Field("MAX", self._to_str(max_item)),
            ],
            "weekly_data": json.dumps(weekly_data),
            "last_week_data": json.dumps(last_week_data),
        }

    def model_to_view(self, primitive: BloodGlucose) -> dict:
        return {
            "date": utc_str_field_to_val(primitive.startDateTime),
            BloodGlucose.VALUE: primitive.get_value_by_unit(self.units),
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
            "dateRange": get_date_range_str(self.start_date_time, self.end_date_time),
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
                {"day": day, **build_deviation_dict(scores, self.min, self.max)}
            )

        for key, values in last_week_data.items():
            if len(values) > 3:
                values[:] = values[-3:]
        last_week_data = self._grouped_data_to_array(last_week_data)
        return {
            "ragThresholds": rag,
            "dateRange": get_date_range_str(
                self._get_first_day(last_week_data), last_primitive_date
            ),
            "data": last_week_data,
            "deviationData": deviation_data_view,
        }

    def _get_median_field(self, primitives: list[BloodGlucose]):
        median = self._calculate_median(primitives)
        return Field(
            '6 month median<span class="superscripts">*<span>2</span></span>',
            f"{median} " f"{self.units.value}",
        )

    @staticmethod
    def _extract_min_max_values(
        primitives: list[BloodGlucose],
    ) -> (BloodGlucose, BloodGlucose):
        min_item = min(
            primitives,
            key=lambda p: (p.value, -p.startDateTime.timestamp()),
        )
        max_item = max(primitives, key=lambda p: (p.value, p.startDateTime.timestamp()))
        return min_item, max_item

    def _calculate_mean_with_deviation(
        self,
        items: list[BloodGlucose],
        date: Optional[str],
        date_field_name="day",
    ) -> dict[str, Union[float, datetime]]:
        """Calculate a median value from primitives"""
        if not items:
            day_date = datetime.strptime(date, date_frmt)
            if date:
                return {date_field_name: utc_str_field_to_val(day_date)}
            return {}

        day_date = datetime.strptime(date, date_frmt)
        scores = [x.get_value_by_unit(self.units) for x in items]
        mean = statistics.mean(scores)
        result = {
            BloodGlucose.VALUE: round_half_up(mean, 1),
            date_field_name: utc_str_field_to_val(day_date),
        }
        if len(scores) >= 2:
            result.update(build_deviation_dict(scores, self.min, self.max))

        return remove_none_values(result)

    def _calculate_median(self, items: list[BloodGlucose]):
        median = statistics.median([x.get_value_by_unit(self.units) for x in items])
        return round_half_up(median, 1)

    def _to_str(self, blood_glucose: BloodGlucose) -> str:
        return (
            f"{round_half_up(blood_glucose.get_value_by_unit(self.units), 1)} "
            f"{self.units.value} "
            f"({blood_glucose.startDateTime.strftime('%d %b')})"
        )

    @staticmethod
    def _build_rag(rag: list[RagThreshold], units: MeasureUnit) -> list[dict]:
        for rag_item in rag:
            if (
                not rag_item.enabled
                or not units
                or units is MeasureUnit.MILLIMOLES_PER_LITRE.value
            ):
                continue

            convert = BloodGlucose.UNITS_CONVERTERS_MAP.get(units)
            if not convert:
                continue

            for item in rag_item.thresholdRange or []:
                if item.minValue:
                    item.minValue = convert(item.minValue)
                if item.maxValue:
                    item.maxValue = convert(item.maxValue)

        return [rag_item.to_dict(include_none=False) for rag_item in rag]
