import unittest

from extensions.deployment.router.inbox_request import (
    SendMessageToPatientListRequestObject,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_VALID_OBJECT_ID = "60a20766c85cd55b38c99e12"


class MessageToPatientListRequestObjectTestCase(unittest.TestCase):
    def test_success_send_message_to_user_list_object(self):
        try:
            SendMessageToPatientListRequestObject.from_dict(
                {
                    SendMessageToPatientListRequestObject.USER_IDS: [
                        SAMPLE_VALID_OBJECT_ID
                    ],
                    SendMessageToPatientListRequestObject.SUBMITTER_ID: SAMPLE_VALID_OBJECT_ID,
                    SendMessageToPatientListRequestObject.SUBMITTER_NAME: "name",
                    SendMessageToPatientListRequestObject.ALL_USERS: False,
                    SendMessageToPatientListRequestObject.TEXT: "text",
                    SendMessageToPatientListRequestObject.CUSTOM: True,
                }
            )
        except ConvertibleClassValidationError as e:
            self.fail(e)

    def test_failure_send_message_to_user_list_object_with_empty_list(self):
        with self.assertRaises(ConvertibleClassValidationError):
            SendMessageToPatientListRequestObject.from_dict(
                {
                    SendMessageToPatientListRequestObject.USER_IDS: [],
                    SendMessageToPatientListRequestObject.SUBMITTER_ID: SAMPLE_VALID_OBJECT_ID,
                    SendMessageToPatientListRequestObject.SUBMITTER_NAME: "name",
                    SendMessageToPatientListRequestObject.ALL_USERS: False,
                    SendMessageToPatientListRequestObject.TEXT: "text",
                    SendMessageToPatientListRequestObject.CUSTOM: True,
                }
            )

    def test_failure_send_message_to_user_list_object_with_lost_required_all_users(
        self,
    ):
        with self.assertRaises(ConvertibleClassValidationError):
            SendMessageToPatientListRequestObject.from_dict(
                {
                    SendMessageToPatientListRequestObject.SUBMITTER_ID: SAMPLE_VALID_OBJECT_ID,
                    SendMessageToPatientListRequestObject.SUBMITTER_NAME: "name",
                    SendMessageToPatientListRequestObject.ALL_USERS: False,
                    SendMessageToPatientListRequestObject.TEXT: "text",
                    SendMessageToPatientListRequestObject.CUSTOM: True,
                }
            )
