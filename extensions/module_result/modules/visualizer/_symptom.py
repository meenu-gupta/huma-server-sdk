from collections import OrderedDict, Counter
from copy import deepcopy
from datetime import datetime
from functools import cached_property

from dateutil import rrule

from extensions.module_result.models.primitives import Primitives, Primitive
from extensions.module_result.modules.visualizer import HTMLVisualizer

_SymptomName = _Date = str
_SymptomData = dict[_Date, Counter]
_SymptomsView = dict[_SymptomName, _SymptomData]


class SymptomHTMLVisualizer(HTMLVisualizer):
    template_name = "symptom.html"
    TOP_REPORTED_SYMPTOMS = 2

    def get_context(self) -> dict:
        config = self.module.find_config(self.deployment.moduleConfigs, None)
        if not config:
            return {}

        with self.module.configure(config):
            primitives = self._fetch_primitives()
            symptoms: _SymptomsView = self._sort_symptoms_by_total_count(
                self._to_symptoms_view(primitives)
            )
            all_symptoms = {s["name"] for s in self._predefined_symptoms()}
            structured_symptoms = self._structure_symptoms(symptoms)

        reported_symptoms = self._count_and_format_symptoms(symptoms)
        not_reported_symptoms = [s for s in all_symptoms if s not in symptoms]

        return {
            "top_reported_symptoms": structured_symptoms[: self.TOP_REPORTED_SYMPTOMS],
            "reported_symptoms": reported_symptoms[self.TOP_REPORTED_SYMPTOMS :],
            "not_reported_symptoms": not_reported_symptoms,
        }

    def _to_symptoms_view(self, primitives: Primitives) -> _SymptomsView:
        """
        Groups symptoms by name and month reported and counts number of each severity for each symptom.
        Result dict includes all months between first and last records,
        even if nothing was reported during these months.
        """
        symptoms = OrderedDict()
        months_dict = self._months_dict(self.start_date_time, self.end_date_time)
        for primitive in primitives:
            month = primitive.startDateTime.strftime("%b")

            for symptom in primitive.complexValues or []:
                is_valid_symptom = (
                    symptom.name in self._name_to_severity_map
                    and symptom.severity in self._name_to_severity_map[symptom.name]
                )
                if not is_valid_symptom:
                    continue

                inner = symptoms.setdefault(symptom.name, deepcopy(months_dict))
                severity = self._name_to_severity_map[symptom.name][symptom.severity]
                inner[month][severity.lower()] += 1

        return symptoms

    @cached_property
    def _name_to_severity_map(self) -> dict[str, dict[str, str]]:
        return {
            s["name"]: OrderedDict(
                sorted(
                    ((option["severity"], option["value"]) for option in s["scale"]),
                    key=lambda s: s[0],
                )
            )
            for s in self._predefined_symptoms()
        }

    def _structure_symptoms(self, symptoms: _SymptomsView):
        severities_map = {
            name: severity
            for severities in self._name_to_severity_map.values()
            for severity, name in severities.items()
        }
        severities = self._format_severities(severities_map)
        structured_symptoms = []
        for symptom, data in symptoms.items():
            symptoms_data = [
                {"month": month, **severities} for month, severities in data.items()
            ]
            structured_symptoms.append(
                {
                    "data": symptoms_data,
                    "dateRange": self._get_date_range_str(
                        self.start_date_time, self.end_date_time
                    ),
                    "severityList": severities,
                    "title": symptom,
                }
            )
        return structured_symptoms

    def _predefined_symptoms(self):
        symptoms = self.module.config.get_config_body().get("complexSymptoms", [])
        for symptom in symptoms:
            if scale := symptom.get("scale"):
                for item in scale:
                    item["value"] = item["value"].strip()
        return symptoms

    @staticmethod
    def _sort_symptoms_by_total_count(symptoms: _SymptomsView) -> _SymptomsView:
        items: tuple = tuple(symptoms.items())
        return OrderedDict(sorted(items, key=lambda d: _count(d[1]), reverse=True))

    @staticmethod
    def _months_dict(start: datetime, until: datetime):
        monthly_rule = rrule.rrule(
            freq=rrule.MONTHLY, dtstart=start, until=until, bymonthday=-1
        )
        result = OrderedDict(
            {month.strftime("%b"): Counter() for month in monthly_rule}
        )
        last_month = until.strftime("%b")
        result[last_month] = Counter()
        return result

    @staticmethod
    def _count_and_format_symptoms(symptoms: _SymptomsView) -> list:
        return [
            {"name": name, "count": _count(data)} for name, data in symptoms.items()
        ]

    @staticmethod
    def _format_severities(severities_map: dict[str, str]) -> list:
        return [
            {"title": name, "name": name.lower(), "severity": severity}
            for name, severity in severities_map.items()
        ]

    @staticmethod
    def _get_date_range_str(start, end) -> str:
        return f"{start.strftime('%d %b')} - {end.strftime('%d %b')}"

    def model_to_view(self, primitive: Primitive) -> dict:
        pass


def _count(items: _SymptomData):
    return sum(sum(data.values()) for data in items.values())
