import unittest
from pathlib import Path

from bson import ObjectId
from werkzeug.test import TestResponse

from sdk.auth.component import AuthComponent
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.utils.validators import remove_none_values
from sdk.inbox.component import InboxComponent
from sdk.inbox.models.confirm_message import (
    ConfirmMessageRequestObject,
    ConfirmMessageResponseObject,
)
from sdk.inbox.models.message import Message, MessageStatusType
from sdk.inbox.models.search_message import (
    MessageSearchRequestObject,
    MessageSearchResponseObject,
)
from sdk.notification.component import NotificationComponent
from sdk.tests.test_case import SdkTestCase

USER_ID_1 = "5e8f0c74b50aa9656c34789a"
USER_ID_2 = "5e84b0dab8dfa268b1180536"
USER_ID_3 = "5e8f0c31b50aa9656c34789a"
MANAGER_ID = "5e8f0c74b50aa9656c44789d"


class InboxTestCase(SdkTestCase):
    components = [AuthComponent(), NotificationComponent(), InboxComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/users_dump.json")]

    @staticmethod
    def _model_send_message_request(text: str, custom: bool = None):
        return remove_none_values({Message.TEXT: text, Message.CUSTOM: custom})

    def _send_message(
        self, sender_id: str, receiver_id: str, message_body: str, custom: bool = False
    ):
        body = self._model_send_message_request(message_body, custom)
        return self.flask_client.post(
            f"/api/inbox/v1beta/user/{receiver_id}/message/send",
            headers=self.get_headers_for_token(sender_id),
            json=body,
        )

    def _validate_invalid_request_exception(self, rsp: TestResponse):
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.json["code"], ErrorCodes.INVALID_REQUEST)

    def test_failure_send_message_with_empty_body(self):
        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/user/{USER_ID_1}/message/send",
            headers=self.get_headers_for_token(USER_ID_2),
            json={},
        )
        self._validate_invalid_request_exception(rsp)

    def test_failure_search_messages_with_empty_body(self):
        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/user/{USER_ID_1}/message/search",
            headers=self.get_headers_for_token(USER_ID_2),
            json={},
        )
        self._validate_invalid_request_exception(rsp)

    def test_failure_search_messages_with_invalid_object_id(self):
        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/user/{USER_ID_1}/message/search",
            headers=self.get_headers_for_token(USER_ID_2),
            json={MessageSearchRequestObject.SUBMITTER_ID: "submitter_id"},
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_confirm_messages(self):
        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/message/confirm",
            headers=self.get_headers_for_token(USER_ID_1),
            json={},
        )
        self._validate_invalid_request_exception(rsp)

    def _receive_messages(
        self,
        sender_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        custom: bool = False,
    ):
        body = {
            MessageSearchRequestObject.SUBMITTER_ID: sender_id,
            MessageSearchRequestObject.SKIP: skip,
            MessageSearchRequestObject.LIMIT: limit,
            MessageSearchRequestObject.CUSTOM: custom,
        }
        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/user/{user_id}/message/search",
            headers=self.get_headers_for_token(sender_id),
            json=body,
        )
        return rsp

    def _send_several_messages(self):
        test_body_message_1 = "test body message 1"
        test_body_message_2 = "test body message 2"
        self._send_message(USER_ID_1, USER_ID_2, test_body_message_1)
        self._send_message(USER_ID_1, USER_ID_2, test_body_message_2)
        self._send_message(USER_ID_1, USER_ID_2, test_body_message_1)
        self._send_message(USER_ID_3, USER_ID_2, test_body_message_2)
        self._send_message(USER_ID_3, USER_ID_2, test_body_message_2, custom=True)
        self._send_message(USER_ID_3, USER_ID_2, test_body_message_1)

    def _confirm_messages(self, user_id: str, message_ids: list[str]):
        request_obj = ConfirmMessageRequestObject(message_ids)
        body = request_obj.to_dict()
        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/message/confirm",
            headers=self.get_headers_for_token(user_id),
            json=body,
        )
        return rsp

    def test_send_message(self):
        rsp = self._send_message(USER_ID_1, USER_ID_2, "test body message")
        self.assertEqual(201, rsp.status_code)
        return rsp.json

    def test_send_and_search_messages(self):
        test_body_message_1 = "test body message 1"
        test_body_message_2 = "test body message 2"
        rsp = self._send_message(USER_ID_1, USER_ID_2, test_body_message_1)
        self.assertEqual(201, rsp.status_code)
        rsp = self._send_message(USER_ID_1, USER_ID_2, test_body_message_2)
        self.assertEqual(201, rsp.status_code)

        rsp = self._send_message(USER_ID_3, USER_ID_2, test_body_message_2)
        self.assertEqual(201, rsp.status_code)

        rsp = self._receive_messages(USER_ID_1, USER_ID_2)
        self.assertEqual(200, rsp.status_code)

        messages = rsp.json[MessageSearchResponseObject.MESSAGES]
        senders = set([m[Message.SUBMITTER_ID] for m in messages])
        self.assertEqual(1, len(senders))
        self.assertIn(USER_ID_1, senders)

        receivers = set([m[Message.USER_ID] for m in messages])
        self.assertEqual(1, len(receivers))
        self.assertIn(USER_ID_2, receivers)

        message_bodies = set([m[Message.TEXT] for m in messages])
        self.assertIn(test_body_message_1, message_bodies)
        self.assertIn(test_body_message_2, message_bodies)

    def test_message_count(self):
        self._send_several_messages()
        rsp = self._receive_messages(USER_ID_1, USER_ID_2)
        self.assertEqual(200, rsp.status_code)
        self.assertTrue(len(rsp.json["messages"]) >= 3)
        rsp = self._receive_messages(USER_ID_3, USER_ID_2)
        self.assertEqual(200, rsp.status_code)
        self.assertTrue(len(rsp.json["messages"]) >= 2)

    def test_successful_message_confirm(self):
        test_body_message = "test body message 1"
        rsp = self._send_message(USER_ID_1, USER_ID_2, test_body_message)
        message_id = rsp.json["id"]
        rsp = self._receive_messages(USER_ID_1, USER_ID_2, 0, 1)
        message: Message = Message.from_dict(
            rsp.json[MessageSearchResponseObject.MESSAGES][0]
        )
        self.assertEqual(MessageStatusType.DELIVERED, message.status)
        rsp = self._confirm_messages(USER_ID_2, [message_id])
        self.assertEqual(201, rsp.status_code)
        self.assertEqual(1, rsp.json[ConfirmMessageResponseObject.UPDATED])
        rsp = self._receive_messages(USER_ID_1, USER_ID_2, 0, 1)
        message: Message = Message.from_dict(
            rsp.json[MessageSearchResponseObject.MESSAGES][0]
        )
        self.assertEqual(MessageStatusType.READ, message.status)

    def test_unsuccessful_message_confirm(self):
        test_body_message = "test body message 1"
        rsp = self._send_message(USER_ID_1, USER_ID_2, test_body_message)
        message_id = rsp.json["id"]
        rsp = self._confirm_messages(USER_ID_1, [message_id])
        self.assertEqual(401, rsp.status_code)

    def test_summary(self):
        self._send_several_messages()

        rsp = self._receive_summary(USER_ID_2, USER_ID_2)
        self.assertEqual(200, rsp.status_code)

        messages = rsp.json["messages"]
        message_id = messages[0]["latestMessage"]["id"]
        first_set_unread_count = messages[0]["unreadMessageCount"]
        self._confirm_messages(USER_ID_2, [message_id])

        rsp = self._receive_summary(USER_ID_2, USER_ID_2)
        self.assertEqual(200, rsp.status_code)

        messages = rsp.json["messages"]
        second_set_unread_count = messages[0]["unreadMessageCount"]
        self.assertEqual(first_set_unread_count - 1, second_set_unread_count)

        self.assertEqual(3, len(messages))
        self.assertFalse(messages[0][Message.CUSTOM])
        self.assertTrue(messages[1][Message.CUSTOM])
        self.assertFalse(messages[2][Message.CUSTOM])

    def test_summary_with_no_custom_flag(self):
        new_message = "New Message Text"
        rsp = self._send_message(USER_ID_1, USER_ID_2, "Old Message Text")
        self._send_message(USER_ID_1, USER_ID_2, "New Message Text")
        old_message_id = rsp.json["id"]
        self.mongo_database.inbox.update_one(
            {"_id": ObjectId(old_message_id)},
            {"$unset": {"custom": ""}},
        )

        rsp = self._receive_summary(USER_ID_2, USER_ID_2)
        self.assertEqual(200, rsp.status_code)

        messages = rsp.json["messages"]
        self.assertEqual(2, len(messages))
        self.assertEqual(new_message, messages[0]["latestMessage"]["text"])

    def _receive_summary(self, user_id: str, caller_id: str):
        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/user/{user_id}/message/summary/search",
            headers=self.get_headers_for_token(caller_id),
        )
        return rsp

    def test_failure_passing_malformed_message_ids(self):
        rsp = self._confirm_messages(USER_ID_1, ["wrongmessageid"])
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_send_custom_message(self):
        message = "custom"
        rsp = self._send_message(USER_ID_1, USER_ID_2, message, custom=True)
        self.assertEqual(201, rsp.status_code)
        msg_id = rsp.json["id"]

        rsp = self._receive_messages(USER_ID_1, USER_ID_2, custom=True)
        self.assertEqual(200, rsp.status_code)

        messages = rsp.json[MessageSearchResponseObject.MESSAGES]
        self.assertEqual(messages[0][Message.ID], msg_id)
        self.assertTrue(messages[0][Message.CUSTOM])

    def test_retrieve_custom_messages(self):
        self._send_several_messages()
        rsp = self._receive_messages(USER_ID_3, USER_ID_2, custom=True)
        self.assertEqual(200, rsp.status_code)

        messages = rsp.json[MessageSearchResponseObject.MESSAGES]
        self.assertEqual(1, len(messages))
        self.assertTrue(messages[0][Message.CUSTOM])


if __name__ == "__main__":
    unittest.main()
