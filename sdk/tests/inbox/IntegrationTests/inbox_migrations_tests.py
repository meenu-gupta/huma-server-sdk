from pathlib import Path
from typing import Union

from sdk.auth.component import AuthComponent
from sdk.inbox.component import InboxComponent
from sdk.inbox.models.message import Message
from sdk.inbox.repo.models.mongo_message import MongoMessageDocument
from sdk.notification.component import NotificationComponent
from sdk.tests.test_case import SdkTestCase
from tools.mongodb_script.add_message_to_deployment_without_message import (
    set_default_custom_flag_for_messages,
)


class InboxMigrationsTestCase(SdkTestCase):
    components = [AuthComponent(), NotificationComponent(), InboxComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/users_dump.json")]

    def _get_messages(self, custom: Union[bool, None]):
        query = {Message.CUSTOM: custom}
        return self.mongo_database[MongoMessageDocument.INBOX_COLLECTION].find(query)

    def test_set_default_custom_flag_for_messages(self):
        old_messages = self._get_messages(None)
        self.assertEqual(1, len(list(old_messages)))
        predefined_messages = self._get_messages(False)
        self.assertEqual(0, len(list(predefined_messages)))

        set_default_custom_flag_for_messages(self.mongo_database)

        old_messages = self._get_messages(None)
        self.assertEqual(0, len(list(old_messages)))
        predefined_messages = self._get_messages(False)
        self.assertEqual(1, len(list(predefined_messages)))
