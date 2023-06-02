import json
import statistics
from collections import OrderedDict
from datetime import datetime
from typing import Optional, Union

from dateutil import rrule
from dateutil.relativedelta import relativedelta

from extensions.module_result.models.primitives import BloodPressure
from extensions.module_result.modules.visualizer import HTMLVisualizer, Field, date_frmt
from sdk.common.utils.common_functions_utils import round_half_up
from sdk.common.utils.validators import utc_str_field_to_val, remove_none_values


class BloodPressureHTMLVisualizer(HTMLVisualizer):
    TITLE = "Blood Pressure"
    template_name = "blood_pressure.html"

    def get_context(self) -> dict:
        config = self.module.find_config(self.deployment.moduleConfigs, None)
        if not config:
            return {}

        with self.module.configure(config):
            primitives: list[BloodPressure] = self._fetch_primitives()  # noqa
            if not primitives:
                return {}

        rag = [item.to_dict() for item in config.ragThresholds or []]

        weekly_data = self._build_big_chart_view(primitives, rag)
        last_week_data = self._build_small_chart_view(primitives, rag)
        # build miscellaneous
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
            "legend": [
                Field(
                    "Systolic blood pressure",
                    '<div class="dark-dot title-dot-margin"></div>',
                ),
                Field(
                    "Diastolic blood pressure",
                    '<div class="white-dot title-dot-margin"></div>',
                ),
            ],
        }

    def _build_big_chart_view(self, primitives, rag):
        weekly_data = self._build_weekly_view(
            primitives, self.start_date_time, self.end_date_time
        )
        weekly_data_view = [
            self._calculate_median_item(items, date)
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
        last_week_data = self._grouped_data_to_array(last_week_data)
        return {
            "ragThresholds": rag,
            "dateRange": self._get_date_range_str(
                self._get_first_day(last_week_data, BloodPressure.START_DATE_TIME),
                last_primitive_date,
            ),
            "data": last_week_data,
        }

    def _slice_data_by_date(
        self, primitives: list[BloodPressure], start, end
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

            daily_data[day_str].append(primitive)

        for day, data in daily_data.items():
            if not data:
                continue

            if len(data) > 3:
                data[:] = data[-3:]
            data.sort(key=lambda p: p.startDateTime)
            data[:] = [self.model_to_view(p) for p in data]

        return daily_data

    def _get_median_field(self, primitives: list[BloodPressure]):
        primitives.sort(key=lambda p: p.createDateTime, reverse=True)
        median = self._calculate_median_item(primitives, None)
        systolic = round_half_up(median[BloodPressure.SYSTOLIC_VALUE])
        diastolic = round_half_up(median[BloodPressure.DIASTOLIC_VALUE])
        return Field(
            '6 month median<span class="superscripts">*<span>2</span></span>',
            f"{systolic}/{diastolic} " f"{primitives[0].diastolicValueUnit}",
        )

    @staticmethod
    def _extract_min_max_values(
        primitives: list[BloodPressure],
    ) -> (BloodPressure, BloodPressure):
        primitives.sort(key=lambda p: (-p.systolicValue, p.startDateTime), reverse=True)
        min_item = primitives[0]
        primitives.sort(key=lambda p: (p.systolicValue, p.startDateTime), reverse=True)
        max_item = primitives[0]
        return min_item, max_item

    @staticmethod
    def _calculate_median_item(
        items: list[BloodPressure], date: Optional[datetime]
    ) -> dict[str, Union[float, datetime]]:
        """
        Calculate a median value for systolic and diastolic blood pressure from primitives
        based on this formula:
        https://www.statisticshowto.com/probability-and-statistics/statistics-definitions/median/
        """
        if not items:
            if date:
                return {BloodPressure.START_DATE_TIME: date}
            return {}

        items.sort(key=lambda x: x.systolicValue)
        median_diastolic = statistics.median([x.diastolicValue for x in items])
        median_systolic = statistics.median([x.systolicValue for x in items])
        result = {
            BloodPressure.DIASTOLIC_VALUE: median_diastolic,
            BloodPressure.SYSTOLIC_VALUE: median_systolic,
            BloodPressure.START_DATE_TIME: date,
        }
        return remove_none_values(result)

    @staticmethod
    def _get_date_range_str(start, end) -> str:
        return f"{start.strftime('%d %b')} - {end.strftime('%d %b')}"

    def model_to_view(self, primitive: BloodPressure) -> dict:
        return {
            BloodPressure.START_DATE_TIME: utc_str_field_to_val(
                primitive.startDateTime
            ),
            BloodPressure.DIASTOLIC_VALUE: primitive.diastolicValue,
            BloodPressure.SYSTOLIC_VALUE: primitive.systolicValue,
        }

    @staticmethod
    def _to_str(blood_pressure: BloodPressure) -> str:
        return (
            f"{blood_pressure.systolicValue}/{blood_pressure.diastolicValue} "
            f"{blood_pressure.diastolicValueUnit} "
            f"({blood_pressure.startDateTime.strftime('%d %b')})"
        )

    @staticmethod
    def _grouped_data_to_array(grouped_data: OrderedDict):
        result = []
        for day, values in grouped_data.items():
            if values:
                result.extend(values)
            else:
                day = datetime.strptime(day, date_frmt)
                result.append(
                    {BloodPressure.START_DATE_TIME: utc_str_field_to_val(day)}
                )

        return result
