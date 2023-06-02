from pathlib import Path

from bson import ObjectId

from apps.ppserver.callbacks.inbox_auth import setup_inbox_send_auth
from apps.ppserver.tests.test_case import AppsTestCase


from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from sdk.auth.component import AuthComponent
from sdk.inbox.component import InboxComponent
from sdk.inbox.events.auth_events import InboxSendAuthEvent
from sdk.inbox.models.message import Message, SubmitterMessageReport
from sdk.inbox.models.search_message import (
    MessageSearchRequestObject,
    MessageSearchResponseObject,
)
from sdk.inbox.repo.models.mongo_message import MongoMessageDocument
from sdk.notification.component import NotificationComponent
from sdk.versioning.component import VersionComponent

USER_1_ID_DEPLOYMENT_X = "5e8f0c74b50aa9656c34789b"
MANAGER_1_ID_DEPLOYMENT_X = "5e8f0c74b50aa9656c34789d"
USER_1_ID_DEPLOYMENT_Y = "5eda5e367adadfb46f7ff71f"


class InboxTestCase(AppsTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        NotificationComponent(),
        InboxComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
    ]

    def setUp(self):
        super().setUp()

    @staticmethod
    def _model_send_message_request(text: str):
        return {Message.TEXT: text}

    def _send_message(self, sender_id: str, receiver_id: str, message_body: str):
        body = self._model_send_message_request(message_body)
        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/user/{receiver_id}/message/send",
            headers=self.get_headers_for_token(sender_id),
            json=body,
        )
        return rsp

    def test_send_message_user_from_same_deployment(self):
        self.test_server.event_bus.subscribe(InboxSendAuthEvent, setup_inbox_send_auth)

        rsp = self._send_message(
            MANAGER_1_ID_DEPLOYMENT_X, USER_1_ID_DEPLOYMENT_X, "text_message"
        )
        self.assertEqual(201, rsp.status_code)

    def test_send_message_user_from_other_deployment(self):
        self.test_server.event_bus.subscribe(InboxSendAuthEvent, setup_inbox_send_auth)

        rsp = self._send_message(
            MANAGER_1_ID_DEPLOYMENT_X, USER_1_ID_DEPLOYMENT_Y, "text_message"
        )
        self.assertEqual(403, rsp.status_code)

    def test_send_multilanguage_message_en(self):
        self.test_server.event_bus.subscribe(InboxSendAuthEvent, setup_inbox_send_auth)

        rsp = self._send_message(
            MANAGER_1_ID_DEPLOYMENT_X,
            USER_1_ID_DEPLOYMENT_X,
            "Some EN translated message",
        )
        self.assertEqual(201, rsp.status_code)

        msg_in_db = self.mongo_database["inbox"].find_one(
            {MongoMessageDocument.ID_: ObjectId(rsp.json["id"])}
        )
        self.assertEqual("hu_sample_message", msg_in_db[Message.TEXT])

        body = {
            MessageSearchRequestObject.SUBMITTER_ID: MANAGER_1_ID_DEPLOYMENT_X,
            MessageSearchRequestObject.USER_ID: USER_1_ID_DEPLOYMENT_X,
            MessageSearchRequestObject.SKIP: 0,
            MessageSearchRequestObject.LIMIT: 100,
        }
        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/message/search",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
            json=body,
        )
        self.assertEqual(
            "Some EN translated message",
            rsp.json[MessageSearchResponseObject.MESSAGES][0][Message.TEXT],
        )

        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/message/summary/search",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
            json=body,
        )
        self.assertEqual(
            "Some EN translated message",
            rsp.json[MessageSearchResponseObject.MESSAGES][0][
                SubmitterMessageReport.LATEST_MESSAGE
            ][Message.TEXT],
        )
