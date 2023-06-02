import datetime
import unittest
from unittest.mock import MagicMock

from extensions.key_action.use_case.key_action_requests import (
    RetrieveKeyActionsTimeframeRequestObject,
)
from extensions.tests.key_actions.test_utils import Samples
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.validators import utc_str_val_to_field


class RetrieveKeyActionTimeframeRequestObjectTestCase(unittest.TestCase):
    def setUp(self) -> None:
        user = MagicMock()
        user.organization_ids.return_value = []
        user.deployment_ids.return_value = "60a35bc8a7e74a19a630af7c"
        self.request_obj = RetrieveKeyActionsTimeframeRequestObject(
            user=user,
            start=utc_str_val_to_field("2020-12-31T23:59:00.000Z"),
            end=utc_str_val_to_field("2021-01-01T00:00:00.000Z"),
            userId="a733671100cd26d816eed39507",
            timezone="Europe/London",
        )

    def test_success_retrieve_key_action(self):
        self.assertTrue(isinstance(self.request_obj.start, datetime.datetime))
        self.assertTrue(isinstance(self.request_obj.end, datetime.datetime))

    def test_failure_retrieve_key_action_start_greater_than_end(self):
        request_body = Samples.retrieve_key_actions_timeframe_request_body()
        request_body.update({"start": "2021-01-01T01:00:00.000Z"})
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveKeyActionsTimeframeRequestObject.from_dict(request_body)

    def test_failure_retrieve_key_action_no_start(self):
        request_body = Samples.retrieve_key_actions_timeframe_request_body()
        request_body.pop("start")
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveKeyActionsTimeframeRequestObject.from_dict(request_body)

    def test_failure_retrieve_key_action_no_end(self):
        request_body = Samples.retrieve_key_actions_timeframe_request_body()
        request_body.pop("end")
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveKeyActionsTimeframeRequestObject.from_dict(request_body)

    def test_failure_retrieve_key_action_no_user(self):
        request_body = Samples.retrieve_key_actions_timeframe_request_body()
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveKeyActionsTimeframeRequestObject.from_dict(request_body)
