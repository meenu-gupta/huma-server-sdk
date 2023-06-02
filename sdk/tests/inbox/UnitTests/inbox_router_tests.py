import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.inbox.models.message import Message
from sdk.inbox.router.inbox_router import (
    send_message,
    search_messages,
    summary_messages,
    confirm_messages,
)
from sdk.tests.inbox.UnitTests.common import (
    BaseTestCase,
    USER_ID_2,
    USER_ID_1,
    MOCK_PAYLOAD,
)

testapp = Flask(__name__)
testapp.app_context().push()

INBOX_ROUTER_PATH = "sdk.inbox.router.inbox_router"


class InboxRouterTestCase(BaseTestCase):
    @patch(f"{INBOX_ROUTER_PATH}.jsonify")
    @patch(f"{INBOX_ROUTER_PATH}.g")
    @patch(f"{INBOX_ROUTER_PATH}.InboxService")
    @patch(f"{INBOX_ROUTER_PATH}.Message")
    def test_success_send_message(self, req_obj, service, g_mock, jsonify):
        user_id = USER_ID_2
        submitter_id = USER_ID_1
        g_mock.auth_user = MagicMock()
        g_mock.auth_user.id = submitter_id
        g_mock.authz_user.localization = {}
        g_mock.user_full_name = "Test User"
        payload = MOCK_PAYLOAD
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            send_message(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.SUBMITTER_ID: submitter_id,
                    req_obj.USER_ID: user_id,
                    req_obj.SUBMITTER_NAME: g_mock.user_full_name,
                    req_obj.TEXT: None,
                }
            )
            service().send_message(req_obj.from_dict())
            jsonify.assert_called_with({Message.ID: service().send_message()})

    @patch(f"{INBOX_ROUTER_PATH}.jsonify")
    @patch(f"{INBOX_ROUTER_PATH}.InboxService")
    @patch(f"{INBOX_ROUTER_PATH}.MessageSearchRequestObject")
    def test_success_search_messages(self, req_obj, service, jsonify):
        user_id = USER_ID_1
        payload = MOCK_PAYLOAD
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            search_messages(user_id)
            req_obj.from_dict.assert_called_with({**payload, req_obj.USER_ID: user_id})
            messages = service().retrieve_messages(req_obj.from_dict())
            jsonify.assert_called_with(messages.to_dict())

    def test_failure_search_messages_invalid_object_id(self):
        user_id = USER_ID_1
        payload = {"limit": 10, "skip": 0, "submitterId": "submitterid"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            with self.assertRaises(ConvertibleClassValidationError):
                search_messages(user_id)

    @patch(f"{INBOX_ROUTER_PATH}.InboxService")
    def test_success_retrieve_summary_messages(self, service):
        user_id = USER_ID_1
        payload = MOCK_PAYLOAD
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            summary_messages(user_id)
            service().retrieve_submitters_first_messages.assert_called_with(user_id)

    @patch(f"{INBOX_ROUTER_PATH}.g")
    @patch(f"{INBOX_ROUTER_PATH}.InboxService")
    @patch(f"{INBOX_ROUTER_PATH}.ConfirmMessageResponseObject")
    @patch(f"{INBOX_ROUTER_PATH}.ConfirmMessageRequestObject")
    def test_success_confirm_messages(self, req_obj, rsp_obj, service, g_mock):
        g_mock.auth_user.id = USER_ID_1
        payload = MOCK_PAYLOAD
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            confirm_messages()
            req_obj.from_dict.assert_called_with(payload)
            service().confirm_messages.assert_called_with(
                g_mock.auth_user.id, req_obj.from_dict().messageIds
            )
            rsp_obj.assert_called_with(service().confirm_messages())


if __name__ == "__main__":
    unittest.main()
