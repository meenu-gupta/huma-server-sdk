import unittest

from sdk.inbox.models.search_message import MessageSearchRequestObject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.inbox.router.inbox_request import SendMessageToUserListRequestObject

SAMPLE_VALID_OBJECT_ID = "60a20766c85cd55b38c99e12"


class MessageSearchRequestObjectTestCase(unittest.TestCase):
    def test_success_message_search_request_object(self):
        try:
            MessageSearchRequestObject.from_dict(
                {
                    MessageSearchRequestObject.USER_ID: SAMPLE_VALID_OBJECT_ID,
                    MessageSearchRequestObject.SUBMITTER_ID: SAMPLE_VALID_OBJECT_ID,
                    MessageSearchRequestObject.SKIP: 1,
                    MessageSearchRequestObject.LIMIT: 10,
                }
            )
        except ConvertibleClassValidationError as e:
            self.fail(e)

    def test_failure_message_search_request_object_no_required_field(self):
        with self.assertRaises(ConvertibleClassValidationError):
            MessageSearchRequestObject.from_dict(
                {
                    MessageSearchRequestObject.USER_ID: SAMPLE_VALID_OBJECT_ID,
                    MessageSearchRequestObject.SKIP: 1,
                    MessageSearchRequestObject.LIMIT: 10,
                }
            )

    def test_failure_message_search_request_object_invalid_object_id_field(self):
        with self.assertRaises(ConvertibleClassValidationError):
            MessageSearchRequestObject.from_dict(
                {
                    MessageSearchRequestObject.USER_ID: SAMPLE_VALID_OBJECT_ID,
                    MessageSearchRequestObject.SUBMITTER_ID: "invalid_submitter_id",
                    MessageSearchRequestObject.SKIP: 1,
                    MessageSearchRequestObject.LIMIT: 10,
                }
            )


class MessageToUserListRequestObjectTestCase(unittest.TestCase):
    def test_success_send_message_to_user_list_object(self):
        try:
            SendMessageToUserListRequestObject.from_dict(
                {
                    SendMessageToUserListRequestObject.USER_IDS: [
                        SAMPLE_VALID_OBJECT_ID
                    ],
                    SendMessageToUserListRequestObject.SUBMITTER_ID: SAMPLE_VALID_OBJECT_ID,
                    SendMessageToUserListRequestObject.SUBMITTER_NAME: "name",
                    SendMessageToUserListRequestObject.TEXT: "text",
                    SendMessageToUserListRequestObject.CUSTOM: True,
                }
            )
        except ConvertibleClassValidationError as e:
            self.fail(e)

    def test_failure_send_message_to_user_list_object_with_empty_list(self):
        with self.assertRaises(ConvertibleClassValidationError):
            SendMessageToUserListRequestObject.from_dict(
                {
                    SendMessageToUserListRequestObject.USER_IDS: [],
                    SendMessageToUserListRequestObject.SUBMITTER_ID: SAMPLE_VALID_OBJECT_ID,
                    SendMessageToUserListRequestObject.SUBMITTER_NAME: "name",
                    SendMessageToUserListRequestObject.TEXT: "text",
                    SendMessageToUserListRequestObject.CUSTOM: True,
                }
            )

    def test_failure_send_message_to_user_list_object_with_lost_required_user_ids(
        self,
    ):
        with self.assertRaises(ConvertibleClassValidationError):
            SendMessageToUserListRequestObject.from_dict(
                {
                    SendMessageToUserListRequestObject.SUBMITTER_ID: SAMPLE_VALID_OBJECT_ID,
                    SendMessageToUserListRequestObject.SUBMITTER_NAME: "name",
                    SendMessageToUserListRequestObject.TEXT: "text",
                    SendMessageToUserListRequestObject.CUSTOM: True,
                }
            )


if __name__ == "__main__":
    unittest.main()
