import copy
import unittest
from typing import Any

from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.inbox.models.confirm_message import (
    ConfirmMessageRequestObject,
    ConfirmMessageResponseObject,
)
from sdk.inbox.models.message import Message, SubmitterMessageReport
from sdk.inbox.models.search_message import (
    MessageSearchRequestObject,
    MessageSearchResponseObject,
)
from sdk.tests.inbox.UnitTests.test_samples import (
    sample_submitter_message_report,
    sample_message,
    sample_message_search_request_object,
    sample_message_search_response,
    sample_message_confirmation_response,
    sample_message_confirmation_request,
    SAMPLE_MESSAGE_TEXT,
)


class InboxModelsCreationTestCase(unittest.TestCase):
    def test_success_create_message(self):
        message = Message.from_dict(sample_message())
        self.assertIsNotNone(message)

    def test_success_create_submitter_message_report(self):
        message_report = SubmitterMessageReport.from_dict(
            sample_submitter_message_report()
        )
        self.assertIsNotNone(message_report)

    def test_success_create_message_search_request_object(self):
        message_search = MessageSearchRequestObject.from_dict(
            sample_message_search_request_object()
        )
        self.assertIsNotNone(message_search)

    def test_success_create_message_search_response_object(self):
        message_response = MessageSearchResponseObject.from_dict(
            sample_message_search_response()
        )
        self.assertIsNotNone(message_response)

    def test_success_create_confirm_message_request_object(self):
        confirm_message_request = ConfirmMessageRequestObject.from_dict(
            sample_message_confirmation_request()
        )
        self.assertIsNotNone(confirm_message_request)

    def test_success_create_confirm_message_response_object(self):
        confirm_message_response = ConfirmMessageResponseObject.from_dict(
            sample_message_confirmation_response()
        )
        self.assertIsNotNone(confirm_message_response)

    def test_custom_summary_report(self):
        message_report = SubmitterMessageReport.from_dict(
            sample_submitter_message_report(custom=True)
        )
        self.assertIsNotNone(message_report)
        self.assertEqual(
            SAMPLE_MESSAGE_TEXT,
            message_report.latestMessage.text,
        )


class InboxModelsFieldsValidationTestCase(unittest.TestCase):
    def _check_required_fields(
        self, required_fields: list, test_class: Any, sample_data: dict
    ):
        for field in required_fields:
            data = copy.deepcopy(sample_data)
            data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                test_class.from_dict(data)

    def test_failure_message_text_length_out_of_range(self):
        payload = sample_message()
        payload[Message.TEXT] = "a" * 281
        with self.assertRaises(ConvertibleClassValidationError):
            Message.from_dict(payload)

    def test_failure_missing_required_fields_in_create_message(self):
        required_fields = [
            Message.USER_ID,
            Message.SUBMITTER_ID,
            Message.TEXT,
        ]
        self._check_required_fields(required_fields, Message, sample_message())

    def test_failure_missing_required_fields_in_search_message_request(self):
        required_fields = [
            MessageSearchRequestObject.USER_ID,
            MessageSearchRequestObject.SUBMITTER_ID,
            MessageSearchRequestObject.SKIP,
            MessageSearchRequestObject.LIMIT,
        ]
        self._check_required_fields(
            required_fields,
            MessageSearchRequestObject,
            sample_message_search_request_object(),
        )

    def test_failure_missing_required_fields_in_search_message_response(self):
        required_fields = [
            MessageSearchResponseObject.MESSAGES,
        ]
        self._check_required_fields(
            required_fields,
            MessageSearchResponseObject,
            sample_message_search_response(),
        )

    def test_failure_missing_confirm_message_response_object(self):
        required_fields = [
            ConfirmMessageResponseObject.UPDATED,
        ]
        self._check_required_fields(
            required_fields,
            ConfirmMessageResponseObject,
            sample_message_confirmation_response(),
        )

    def test_failure_missing_confirm_message_request_object(self):
        required_fields = [
            ConfirmMessageRequestObject.MESSAGE_IDS,
        ]
        self._check_required_fields(
            required_fields,
            ConfirmMessageRequestObject,
            sample_message_confirmation_request(),
        )
