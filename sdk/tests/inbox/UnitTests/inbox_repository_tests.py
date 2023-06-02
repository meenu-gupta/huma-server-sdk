from unittest.mock import patch, MagicMock

from bson import ObjectId

from sdk.inbox.models.message import Message, MessageStatusType
from sdk.inbox.repo.models.mongo_message import MongoMessageDocument
from sdk.inbox.repo.mongo_inbox_repository import MongoInboxRepository
from sdk.tests.inbox.UnitTests.common import (
    BaseTestCase,
    USER_ID_1,
    USER_ID_2,
    MESSAGE_ID,
)

INBOX_REPO_PATH = "sdk.inbox.repo.mongo_inbox_repository"
INBOX_COLLECTION = "inbox"


class MongoInboxRepositoryTestCase(BaseTestCase):
    @patch(f"{INBOX_REPO_PATH}.MongoMessageDocument")
    def test_success_create_message(self, document):
        repo = MongoInboxRepository(
            database=MagicMock(), config=MagicMock(), client=MagicMock()
        )
        message = Message.from_dict(
            {
                Message.USER_ID: USER_ID_1,
                Message.SUBMITTER_ID: USER_ID_2,
                Message.TEXT: "test message",
            }
        )
        repo.create_message(message)
        document.assert_called_with(**message.to_dict(include_none=False))

    @patch(f"{INBOX_REPO_PATH}.MongoMessageDocument")
    def test_success_create_message_from_list(self, document):
        db = MagicMock()
        document.__name__ = MongoMessageDocument.__name__
        document.INBOX_COLLECTION = "inbox"
        collection = MagicMock()
        collection.bulk_write.return_value = MagicMock(inserted_count=1)
        collections = {MongoMessageDocument.INBOX_COLLECTION: collection}
        db.__getitem__.side_effect = collections.__getitem__
        repo = MongoInboxRepository(database=db, config=MagicMock(), client=MagicMock())
        message = Message.from_dict(
            {
                Message.USER_ID: USER_ID_1,
                Message.SUBMITTER_ID: USER_ID_2,
                Message.TEXT: "test message",
            }
        )
        repo.create_message_from_list([message])
        collection.bulk_write.assert_called_once()

    @patch(f"{INBOX_REPO_PATH}.MongoMessageDocument")
    def test_success_mark_messages_as_read(self, document):
        repo = MongoInboxRepository(
            database=MagicMock(), config=MagicMock(), client=MagicMock()
        )
        message_owner_id = USER_ID_1
        message_ids = [MESSAGE_ID]
        document.objects().count.return_value = 0

        repo.mark_messages_as_read(message_owner_id, message_ids)
        document.objects.assert_called_with(
            id__in=[ObjectId(MESSAGE_ID)], userId=message_owner_id
        )
        document.objects().update.assert_called_once()

    @patch(f"{INBOX_REPO_PATH}.MongoMessageDocument")
    def test_success_retrieve_submitters_first_messages(self, document):
        repo = MongoInboxRepository(
            database=MagicMock(), config=MagicMock(), client=MagicMock()
        )
        repo.retrieve_submitters_first_messages(user_id=USER_ID_1)
        document.objects.assert_called_with(userId=USER_ID_1)
        document.objects().aggregate.assert_called_once()

    @patch(f"{INBOX_REPO_PATH}.MongoMessageDocument")
    def test_success_retrieve_submitters_all_predefined_messages(self, document):
        repo = MongoInboxRepository(
            database=MagicMock(), config=MagicMock(), client=MagicMock()
        )
        repo.retrieve_submitter_all_messages(
            user_id=USER_ID_1, submitter_id=USER_ID_2, skip=1, limit=2, custom=False
        )
        document.objects.assert_called_with(
            userId=USER_ID_1, submitterId=USER_ID_2, custom=False
        )
        document.objects().order_by.assert_called_once()

    @patch(f"{INBOX_REPO_PATH}.MongoMessageDocument")
    def test_success_retrieve_submitters_all_custom_messages(self, document):
        repo = MongoInboxRepository(
            database=MagicMock(), config=MagicMock(), client=MagicMock()
        )
        repo.retrieve_submitter_all_messages(
            user_id=USER_ID_1, submitter_id=USER_ID_2, skip=1, limit=2, custom=True
        )
        document.objects.assert_called_with(
            userId=USER_ID_1, submitterId=USER_ID_2, custom=True
        )
        document.objects().order_by.assert_called_once()

    @patch(f"{INBOX_REPO_PATH}.MongoMessageDocument")
    def test_success_retrieve_user_unread_messages_count(self, document):
        repo = MongoInboxRepository(
            database=MagicMock(), config=MagicMock(), client=MagicMock()
        )
        repo.retrieve_user_unread_messages_count(user_id=USER_ID_1)
        document.objects.assert_called_with(
            userId=USER_ID_1, status=MessageStatusType.DELIVERED.value
        )
        document.objects().count.assert_called_once()
