from unittest import TestCase

from extensions.key_action.callbacks.key_action_generator import KeyActionGenerator
from sdk.common.utils.date_utils import get_interval_from_duration_iso


class SetFreqTests(TestCase):
    def test_success_set_freq_yearly(self):
        duration = "P6YT1H1M"
        res = KeyActionGenerator.set_freq(duration)
        self.assertEqual(res, 0)

    def test_success_set_freq_monthly(self):
        duration = "P6MT1H1M"
        res = KeyActionGenerator.set_freq(duration)
        self.assertEqual(res, 1)

    def test_success_set_freq_weekly(self):
        duration = "P6WT1H1M"
        res = KeyActionGenerator.set_freq(duration)
        self.assertEqual(res, 2)

    def test_success_set_freq_daily(self):
        duration = "P6DT1H1M"
        res = KeyActionGenerator.set_freq(duration)
        self.assertEqual(res, 3)

    def test_failure_set_freq_unsupported(self):
        duration = "P6PT1H1M"
        with self.assertRaises(Exception):
            KeyActionGenerator.set_freq(duration)


class SetIntervalTests(TestCase):
    def test_success_set_interval_yearly(self):
        duration = "P6YT1H1M"
        res = get_interval_from_duration_iso(duration)
        self.assertEqual(res, 6)

    def test_success_set_interval_monthly(self):
        duration = "P6MT1H1M"
        res = get_interval_from_duration_iso(duration)
        self.assertEqual(res, 6)

    def test_success_set_interval_weekly(self):
        duration = "P6WT1H1M"
        res = get_interval_from_duration_iso(duration)
        self.assertEqual(res, 6)

    def test_success_set_interval_daily(self):
        duration = "P6DT1H1M"
        res = get_interval_from_duration_iso(duration)
        self.assertEqual(res, 6)

    def test_success_set_interval_float_number(self):
        duration = "P6.6DT1H1M"
        res = get_interval_from_duration_iso(duration)
        self.assertEqual(res, 6)

    def test_failure_zero_interval(self):
        duration = "P0DT1H1M"
        with self.assertRaises(ValueError):
            get_interval_from_duration_iso(duration)
