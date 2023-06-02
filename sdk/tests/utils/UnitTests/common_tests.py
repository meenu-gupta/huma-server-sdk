from datetime import datetime
from unittest import TestCase

from freezegun import freeze_time

from sdk.common.push_notifications.push_notifications_utils import (
    _set_notification_data,
)
from sdk.common.utils.common_functions_utils import is_all_items_equal
from sdk.common.utils.validators import datetime_now


class IsAllItemsEqualTestCase(TestCase):
    def test_all_items_equal(self):
        test_array = ["12345", "12345", "12345"]
        self.assertTrue(is_all_items_equal(test_array))

    def test_all_items_equal_one_item(self):
        test_array = ["12345"]
        self.assertTrue(is_all_items_equal(test_array))

    def test_all_items_equal_empty(self):
        test_array = []
        self.assertTrue(is_all_items_equal(test_array))

    def test_all_items_equal_not_equal(self):
        test_array = ["12345", "54321"]
        self.assertFalse(is_all_items_equal(test_array))

    def test_all_items_equal_different_types(self):
        test_array = ["12345", 12345]
        self.assertFalse(is_all_items_equal(test_array))


class ConvertPushDataTestCase(TestCase):
    def test_set_notification_data(self):
        test_dict = {"a": True, "b": "True", "c": False, "d": "False"}
        action = "ACTION"
        now = datetime.now()
        with freeze_time(now):
            now_str = datetime_now()
            data = _set_notification_data(action, test_dict)
        expected_results = {
            "a": "true",
            "b": "True",
            "c": "false",
            "d": "False",
            "action": action,
            "sentDateTime": now_str,
        }
        self.assertDictEqual(expected_results, data)
