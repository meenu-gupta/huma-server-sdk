from datetime import datetime
from unittest import TestCase

import pytz
from dateutil.relativedelta import relativedelta

from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import Deployment
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.modules import BloodPressureModule
from extensions.module_result.modules.visualizer import HTMLVisualizer


class TestVisualizer(HTMLVisualizer):
    def get_context(self) -> dict:
        return {}

    def model_to_view(self, primitive: Primitive) -> dict:
        return {}


class HTMLVisualizerTests(TestCase):
    def test_timezone_is_correct(self):
        user = User(timezone="Asia/Dubai")
        start_date = datetime(2022, 2, 28, 20, 0, 1)
        end_date = start_date + relativedelta(months=6)
        visualizer = TestVisualizer(
            BloodPressureModule(), user, Deployment(), start_date, end_date
        )
        self.assertEqual("Asia/Dubai", visualizer.timezone.zone)
        self.assertEqual(0, visualizer.start_date_time.hour)
        self.assertEqual(0, visualizer.start_date_time.minute)
        self.assertEqual(0, visualizer.start_date_time.second)

        new_end_date = visualizer.end_date_time
        self.assertEqual("Asia/Dubai", new_end_date.tzinfo.zone)
        self.assertEqual(2022, new_end_date.year)
        self.assertEqual(8, new_end_date.month)
        self.assertEqual(start_date.day + 1, new_end_date.day)
        self.assertEqual(0, new_end_date.hour)
        self.assertEqual(0, new_end_date.minute)
        self.assertEqual(1, new_end_date.second)

    def test_build_weeks_array(self):
        timezone = pytz.timezone("Europe/London")
        start_date = datetime(year=2022, month=2, day=10, tzinfo=timezone)
        end_date = start_date + relativedelta(months=3)
        dates = TestVisualizer._build_weeks_array(start_date, end_date, timezone)
        self.assertTrue(all(d.hour == 0 for d in dates))
