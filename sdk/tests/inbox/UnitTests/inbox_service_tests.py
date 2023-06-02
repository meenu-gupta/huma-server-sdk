import unittest
from unittest.mock import patch

from sdk.common.localization.utils import Language
from sdk.inbox.models.message import Message
from sdk.inbox.services.inbox_service import InboxService
from sdk.tests.inbox.UnitTests.common import (
    BaseTestCase,
    USER_ID_1,
    USER_ID_2,
    MESSAGE_ID,
)

INBOX_SERVICE_PATH = "sdk.inbox.services.inbox_service"


class InboxServiceTestCase(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.service = InboxService()

    @patch(f"{INBOX_SERVICE_PATH}.PreCreateMessageEvent")
    @patch(f"{INBOX_SERVICE_PATH}.InboxService._send_push_notification")
    def test_send_message(self, send_push_notification, mocked_event):
        unread_message_count = 1
        message = Message(userId=USER_ID_1, submitterId=USER_ID_2, text="Test message")
        self.inbox_repo.retrieve_user_unread_messages_count.return_value = (
            unread_message_count
        )
        self.service.send_message(message)
        self.event_bus.emit.assert_called_with(mocked_event(), raise_error=True)
        self.inbox_repo.create_message.assert_called_with(message)
        send_push_notification.assert_called_once_with(
            message.userId,
            message.submitterId,
            Language.EN,
            message.custom,
            unread=unread_message_count,
        )

    def test_retrieve_messages(self):
        skip = 0
        limit = 5
        is_custom = True
        self.service.retrieve_messages(USER_ID_1, USER_ID_2, skip, limit, is_custom)
        self.inbox_repo.retrieve_submitter_all_messages.assert_called_with(
            user_id=USER_ID_1,
            submitter_id=USER_ID_2,
            skip=skip,
            limit=limit,
            custom=is_custom,
        )

    def test_retrieve_submitters_first_messages(self):
        user_id = USER_ID_1
        self.service.retrieve_submitters_first_messages(user_id)
        self.inbox_repo.retrieve_submitters_first_messages.assert_called_with(user_id)

    def test_confirm_messages(self):
        message_owner_id = USER_ID_1
        message_ids = [MESSAGE_ID]
        self.service.confirm_messages(message_owner_id, message_ids)
        self.inbox_repo.mark_messages_as_read.assert_called_with(
            message_owner_id, message_ids
        )


if __name__ == "__main__":
    unittest.main()
