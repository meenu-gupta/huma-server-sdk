import unittest
from datetime import datetime, timedelta


from extensions.key_action.models.key_action_log import KeyAction
from extensions.key_action.utils import key_action_to_dict, get_correlated_start_time

VALID_OBJECT_ID = "60019625090d076320280736"


class KeyActionUtilsTestCase(unittest.TestCase):
    def test_key_action_to_dict(self):
        key_action = KeyAction(
            keyActionConfigId=VALID_OBJECT_ID,
            id=VALID_OBJECT_ID,
            title="Test",
            description="Here",
            userId=VALID_OBJECT_ID,
            snoozing=["PT1DM"],
        )
        key_action_dict = key_action_to_dict(key_action)
        self.assertNotIn(KeyAction.SNOOZING, key_action_dict)
        self.assertIsInstance(key_action_dict, dict)

    def test_get_correlated_start_time(self):
        expiration_delta = timedelta(days=1)
        start = datetime.now() - timedelta(days=1)
        end = datetime.now() + timedelta(days=1)
        result = get_correlated_start_time(start, end, expiration_delta)
        self.assertEqual(result, start + expiration_delta)

    def test_get_correlated_start_time_when_start_and_end_equal(self):
        expiration_delta = timedelta(days=1)
        start = end = datetime.now()
        result = get_correlated_start_time(start, end, expiration_delta)
        self.assertEqual(result, end)
