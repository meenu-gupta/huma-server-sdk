from collections import Counter, OrderedDict
from datetime import datetime
from unittest import TestCase, mock

from dateutil.relativedelta import relativedelta

from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import Deployment
from extensions.module_result.models.primitives import Symptom, ComplexSymptomValue
from extensions.module_result.modules import SymptomModule
from extensions.module_result.modules.visualizer import SymptomHTMLVisualizer


severity_map = {
    "Headache": {1: "mild", 2: "moderate", 3: "severe"},
    "Back pain": {1: "mild", 2: "moderate", 3: "severe"},
}


class SymptomHTMLVisualizerTestCase(TestCase):
    @mock.patch.object(SymptomHTMLVisualizer, "_name_to_severity_map", severity_map)
    def test_to_symptoms_view(self):
        primitives = [
            Symptom(
                startDateTime=datetime.utcnow() - relativedelta(months=2),
                complexValues=[
                    ComplexSymptomValue(name="Headache", severity=2),
                    ComplexSymptomValue(name="Back pain", severity=3),
                ],
            ),
            Symptom(
                startDateTime=datetime.utcnow() - relativedelta(months=1),
                complexValues=[
                    ComplexSymptomValue(name="Headache", severity=2),
                    ComplexSymptomValue(name="Back pain", severity=3),
                ],
            ),
        ]
        visualizer = SymptomHTMLVisualizer(
            module=SymptomModule(),
            user=User(),
            deployment=Deployment(),
            start_date_time=datetime.utcnow() - relativedelta(months=6),
            end_date_time=datetime.utcnow(),
        )
        symptoms_view = visualizer._to_symptoms_view(primitives)
        self.assertIn("Headache", symptoms_view)
        self.assertIn("Back pain", symptoms_view)
        self.assertEqual(7, len(symptoms_view["Headache"]))  # current month + delta

    @mock.patch.object(SymptomHTMLVisualizer, "_name_to_severity_map", severity_map)
    def test_structure_symptoms(self):
        symptoms_data = {
            "Sympotom1": {
                "2022-Jan": Counter(mild=5, moderate=2, severe=1),
                "2022-Mar": Counter(mild=5, moderate=2, severe=1),
                "2022-Jun": Counter(mild=2, moderate=5, severe=3),
            },
            "Sympotom2": {
                "2022-Jan": Counter(mild=3, moderate=2, severe=1),
                "2022-Mar": Counter(mild=1, moderate=8, severe=2),
                "2022-Jun": Counter(mild=2, moderate=5, severe=3),
            },
        }
        expected_data = [
            {"month": "2022-Jan", "mild": 5, "moderate": 2, "severe": 1},
            {"month": "2022-Mar", "mild": 5, "moderate": 2, "severe": 1},
            {"month": "2022-Jun", "mild": 2, "moderate": 5, "severe": 3},
        ]
        start = datetime(year=2022, month=1, day=1)
        end = datetime(year=2022, month=6, day=5)
        visualizer = SymptomHTMLVisualizer(None, User(timezone="UTC"), None, start, end)
        result = visualizer._structure_symptoms(symptoms_data)
        test_item = result[0]
        self.assertIn("dateRange", test_item)
        self.assertEqual("Sympotom1", test_item["title"])
        self.assertEqual(expected_data, test_item["data"])

    def test_monthly_dict(self):
        number_of_month = 6
        start = datetime.utcnow()
        end = start + relativedelta(months=number_of_month)
        results = SymptomHTMLVisualizer._months_dict(start, end)
        self.assertEqual(1 + number_of_month, len(results))  # current month + delta

    def test_count_and_format_symptoms(self):
        symptoms_data = {
            "Sympotom1": {
                "2022-Jan": Counter(mild=5, moderate=2, severe=1),
                "2022-Mar": Counter(mild=5, moderate=2, severe=1),
                "2022-Jun": Counter(mild=2, moderate=5, severe=3),
            },
            "Sympotom2": {
                "2022-Jan": Counter(mild=3, moderate=2, severe=1),
                "2022-Mar": Counter(mild=1, moderate=8, severe=2),
                "2022-Jun": Counter(mild=2, moderate=5, severe=3),
            },
        }
        result = SymptomHTMLVisualizer._count_and_format_symptoms(symptoms_data)
        self.assertEqual(2, len(result))
        item1, item2 = result
        self.assertIn("name", item1)
        self.assertEqual(26, item1["count"])
        self.assertIn("name", item2)
        self.assertEqual(27, item2["count"])

    def test_sort_symptoms_by_total_count(self):
        symptoms_data = OrderedDict(
            **{
                "Sympotom1": {
                    "2022-Jan": Counter(mild=5, moderate=2, severe=1),
                    "2022-Mar": Counter(mild=5, moderate=2, severe=1),
                },
                "Sympotom2": {
                    "2022-Jan": Counter(mild=3, moderate=2, severe=1),
                    "2022-Mar": Counter(mild=1, moderate=8, severe=2),
                    "2022-Jun": Counter(mild=2, moderate=5, severe=3),
                },
            }
        )
        result = SymptomHTMLVisualizer._sort_symptoms_by_total_count(symptoms_data)
        self.assertEqual("Sympotom2", next(iter(result)))
