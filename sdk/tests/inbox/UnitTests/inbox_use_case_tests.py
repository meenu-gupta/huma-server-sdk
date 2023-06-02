from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.authorization.models.user import User
from sdk.common.localization.utils import Language
from sdk.inbox.models.message import Message
from sdk.inbox.router.inbox_request import SendMessageToUserListRequestObject
from sdk.inbox.use_case.inbox_use_case import SendMessageToUserListUseCase
from sdk.tests.inbox.UnitTests.common import (
    BaseTestCase,
)

testapp = Flask(__name__)
testapp.app_context().push()

INBOX_USE_CASE_PATH = "sdk.inbox.use_case.inbox_use_case"
SAMPLE_VALID_OBJECT_ID = "60a20766c85cd55b38c99e12"


class SendMessageToUserListUseCaseTestCase(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

    @patch(f"{INBOX_USE_CASE_PATH}.PreCreateMessageEvent")
    @patch(
        f"{INBOX_USE_CASE_PATH}.SendMessageToUserListUseCase._send_push_notification"
    )
    def test_send_message(self, send_push_notification, mocked_event):
        unread_message_count = 1
        self.inbox_repo.retrieve_user_unread_messages_count.return_value = (
            unread_message_count
        )
        request_object = SendMessageToUserListRequestObject.from_dict(
            {
                SendMessageToUserListRequestObject.USER_IDS: [SAMPLE_VALID_OBJECT_ID],
                SendMessageToUserListRequestObject.SUBMITTER_ID: SAMPLE_VALID_OBJECT_ID,
                SendMessageToUserListRequestObject.SUBMITTER_NAME: "name",
                SendMessageToUserListRequestObject.TEXT: "text",
            }
        )
        retrieved_user = User()
        retrieved_user.id = SAMPLE_VALID_OBJECT_ID
        retrieved_user.language = Language.DE
        self.auth_repo.retrieve_users_by_id_list.return_value = [retrieved_user]
        message = Message(
            userId=SAMPLE_VALID_OBJECT_ID,
            submitterId=SAMPLE_VALID_OBJECT_ID,
            submitterName="name",
            text="text",
        )
        message_list = [message]

        SendMessageToUserListUseCase().execute(request_object)
        self.event_bus.emit.assert_called_with(mocked_event(), raise_error=True)
        self.inbox_repo.create_message_from_list.assert_called_with(message_list)
        send_push_notification.assert_called_once_with(
            message.userId,
            message.submitterId,
            retrieved_user.language,
            message.custom,
            unread=unread_message_count,
        )
