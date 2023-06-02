from pathlib import Path
from unittest.mock import patch

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.inbox.component import InboxComponent
from sdk.inbox.repo.models.mongo_message import MongoMessageDocument

VALID_USER_ID = "5ed803dd5f2f99da73684413"


class UserInboxTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        InboxComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/inbox_dump.json")]
    user_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # remove binding from sdk collection if present
        MongoMessageDocument._collection = None

    def test_no_inbox_badges_when_no_messages(self):
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.get(self.user_route, headers=headers)
        self.assertEqual(0, rsp.json["badges"]["messages"])

    def test_inbox_badges(self):
        headers = self.get_headers_for_token(VALID_USER_ID)
        self.create_message()
        rsp = self.flask_client.get(self.user_route, headers=headers)
        self.assertEqual(1, rsp.json["badges"]["messages"])

    def test_no_inbox_badges_when_all_messages_are_read(self):
        headers = self.get_headers_for_token(VALID_USER_ID)
        message_id = self.create_message()
        rsp = self.flask_client.get(self.user_route, headers=headers)
        self.assertEqual(1, rsp.json["badges"]["messages"])
        self.read_message(message_id)
        rsp = self.flask_client.get(self.user_route, headers=headers)
        self.assertEqual(0, rsp.json["badges"]["messages"])

    @patch("sdk.inbox.services.inbox_service.prepare_and_send_push_notification")
    def create_message(self, _):
        headers = self.get_headers_for_token(VALID_USER_ID)
        body = {"userId": VALID_USER_ID, "text": "test message"}
        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/user/{VALID_USER_ID}/message/send",
            json=body,
            headers=headers,
        )
        self.assertEqual(201, rsp.status_code)
        return rsp.json["id"]

    def read_message(self, message_id: str):
        self.mongo_database.inbox.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"status": "READ"}},
        )
