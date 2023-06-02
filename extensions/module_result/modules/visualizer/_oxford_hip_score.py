import json
import statistics
from collections import OrderedDict
from datetime import datetime
from typing import Optional, Union

from dateutil import rrule
from dateutil.relativedelta import relativedelta

from extensions.module_result.models.primitives import OxfordHipScore
from extensions.module_result.modules.visualizer import HTMLVisualizer
from extensions.module_result.modules.visualizer._utils import build_deviation_dict
from sdk.common.utils.common_functions_utils import round_half_up
from sdk.common.utils.validators import remove_none_values, utc_str_field_to_val


class OxfordHipScoreHTMLVisualizer(HTMLVisualizer):
    MAXIMUM_VALUE = 100
    MINIMUM_VALUE = 0
    TITLE = "Oxford Hip Score"
    template_name = "oxford_hip_score.html"

    FIELD_NAMES = [
        OxfordHipScore.LEFT_HIP_SCORE,
        OxfordHipScore.RIGHT_HIP_SCORE,
    ]
    FIELD_TITLES = [
        "Left hip",
        "Right hip",
    ]

    def get_context(self) -> dict:
        config = self.module.find_config(self.deployment.moduleConfigs, None)
        if not config:
            return {}

        with self.module.configure(config):
            primitives: list[OxfordHipScore] = self._fetch_primitives()  # noqa
            if not primitives:
                return {}

        rag = [item.to_dict() for item in config.ragThresholds or []]

        rags = []
        each_primitives = [[], []]
        for ind, field_name in enumerate(self.FIELD_NAMES):
            rags.append([r for r in rag if r.get("fieldName") == field_name])
            each_primitives[ind] = [
                p for p in primitives if p.get_hip_score(field_name, None) is not None
            ]

        weekly_data = self._build_big_chart_view(each_primitives, rags)
        last_week_data = self._build_small_chart_view(each_primitives, rags)
        min_max_items = self._extract_min_max_values(each_primitives)
        data = []
        for ind, field_name in enumerate(self.FIELD_NAMES):
            count = len(each_primitives[ind])
            if each_primitives[ind]:
                min_value = min_max_items[ind]["min_item"].get_hip_score(field_name)
                max_value = min_max_items[ind]["max_item"].get_hip_score(field_name)
                each_data = {
                    "title": config.moduleName or self.TITLE,
                    "subtitle": self.FIELD_TITLES[ind],
                    "unit": "%",
                    "fields": [
                        {
                            "title": "Total number of data points",
                            "value": count,
                        },
                        self._get_median_field(each_primitives[ind], field_name),
                        {
                            "title": "MIN",
                            "value": f"{min_value} ({min_max_items[ind]['min_item'].startDateTime.strftime('%d %b')})",
                        },
                        {
                            "title": "MAX",
                            "value": f"{max_value} ({min_max_items[ind]['max_item'].startDateTime.strftime('%d %b')})",
                        },
                    ],
                    "weekly_data": json.dumps(weekly_data[ind]),
                    "last_week_data": json.dumps(last_week_data[ind]),
                    "isShow": count > 0,
                }
            else:
                each_data = {}
            each_data.update(
                {
                    "weekly_data": json.dumps(weekly_data[ind]),
                    "last_week_data": json.dumps(last_week_data[ind]),
                    "isShow": count > 0,
                }
            )

            data.append(each_data)
        return {"data": data}

    def _build_big_chart_view(self, primitives, rags) -> list:
        date_range = self._get_date_range_str(self.start_date_time, self.end_date_time)
        chart_view = []
        for ind, field_name in enumerate(self.FIELD_NAMES):
            weekly_data = self._build_weekly_view(
                primitives[ind], self.start_date_time, self.end_date_time
            )
            weekly_data_view = [
                self._calculate_mean_item(items, date, field_name, "month")
                for date, items in weekly_data.items()
            ]
            chart_view.append(
                {
                    "ragThresholds": rags[ind],
                    "dateRange": date_range,
                    "data": weekly_data_view,
                }
            )
        return chart_view

    def _build_small_chart_view(self, primitives, rags) -> list:
        hip_scores = []
        for ind, field_name in enumerate(self.FIELD_NAMES):
            if not primitives[ind]:
                hip_scores.append({})
                continue

            last_primitive_date = primitives[ind][-1].startDateTime
            week_ago = last_primitive_date - relativedelta(weeks=1)
            week_data = self._slice_data_by_date(
                primitives[ind],
                start=week_ago,
                end=last_primitive_date,
                field_name=field_name,
            )
            last_week_data, deviation_data_view = self._calculate_scores(week_data)

            hip_scores.append(
                {
                    "ragThresholds": rags[ind],
                    "dateRange": self._get_date_range_str(
                        self._get_first_day(last_week_data), last_primitive_date
                    ),
                    "data": last_week_data,
                    "deviationData": deviation_data_view,
                }
            )

        return hip_scores

    def _calculate_scores(self, last_week_data):
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
        return last_week_data, deviation_data_view

    def _slice_data_by_date(
        self, primitives: list[OxfordHipScore], start, end, field_name=None
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
            data.sort(key=lambda p: p.startDateTime)
            data[:] = [self.model_to_view(p, field_name) for p in data]
            values_for_the_day = [item["value"] for item in data]
            mean = statistics.mean(values_for_the_day)
            for item in data:
                item["middleDayValue"] = round_half_up(mean, 1)
        return daily_data

    @staticmethod
    def _get_median_field(primitives: list[OxfordHipScore], field_name):
        scores = [x.get_hip_score(field_name) for x in primitives]
        median = scores and statistics.median(scores)
        return {
            "title": '6 month median<span class="superscripts">*<span>2</span></span>',
            "value": f"{round_half_up(median)}",
        }

    def _extract_min_max_values(self, primitives: list) -> list:
        min_max_items = []
        for ind, field_name in enumerate(self.FIELD_NAMES):
            if not primitives[ind]:
                min_max_items.append({"min_item": None, "max_item": None})
                continue

            min_item = min(
                primitives[ind],
                key=lambda p: (
                    p.get_hip_score(field_name, int(10e6)),
                    -p.startDateTime.timestamp(),
                ),
            )
            max_item = max(
                primitives[ind],
                key=lambda p: (
                    p.get_hip_score(field_name, int(-10e6)),
                    p.startDateTime.timestamp(),
                ),
            )
            min_max_items.append({"min_item": min_item, "max_item": max_item})

        return min_max_items

    def _calculate_mean_item(
        self,
        items: list[OxfordHipScore],
        date: Optional[datetime],
        field_name: str,
        date_field_name="day",
    ) -> dict[str, Union[float, datetime]]:
        """Calculate a median value from primitives"""
        if not items:
            if date:
                return {date_field_name: date}
            return {}

        scores = [x.get_hip_score(field_name) for x in items]
        mean = statistics.mean(scores)
        result = {"value": mean, date_field_name: date}
        if len(scores) >= 2:
            result.update(
                build_deviation_dict(scores, self.MINIMUM_VALUE, self.MAXIMUM_VALUE)
            )

        return remove_none_values(result)

    @staticmethod
    def _get_date_range_str(start, end) -> str:
        return f"{start.strftime('%d %b')} - {end.strftime('%d %b')}"

    def model_to_view(self, primitive: OxfordHipScore, field_name=None) -> dict:
        return {
            "date": utc_str_field_to_val(primitive.startDateTime),
            "value": primitive.get_hip_score(field_name),
        }
