from pathlib import Path
from typing import Any
from unittest.mock import patch, MagicMock

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.router.user_profile_request import (
    LinkProxyRequestObject,
    UnlinkProxyRequestObject,
)
from extensions.deployment.component import DeploymentComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    USER_1_ID_DEPLOYMENT_X,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.notification.component import NotificationComponent

USER_ID = USER_1_ID_DEPLOYMENT_X
USER_ID_WITHOUT_PROXY = "601919b5c03550c421c075eb"
PROXY_USER_ID = "6192061841fee21a727f8fff"
VALID_CONTRIBUTOR_ID = "60071f359e7e44330f732037"

LINK_PROXY_USE_CASE_PATH = (
    "extensions.authorization.use_cases.proxy_use_cases.LinkProxyUserUseCase"
)
SEND_NOTIFICATION_PATH = f"{LINK_PROXY_USE_CASE_PATH}.send_linked_notification"


class ProxyTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        NotificationComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]

    def setUp(self):
        super(ProxyTestCase, self).setUp()
        self.headers = self.get_headers_for_token(USER_ID)
        self.base_route = "/api/extensions/v1beta/user"

    def post(self, url: str, json: Any, headers: dict = None):
        if not headers:
            headers = self.headers
        return self.flask_client.post(url, json=json, headers=headers)

    def test_link_proxy_use_case__wrong_email(self):
        data = {LinkProxyRequestObject.PROXY_EMAIL: "wrong@email.com"}
        url = f"{self.base_route}/{USER_ID}/assign-proxy"
        rsp = self.post(url, json=data)
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300011, rsp.json["code"])

    @patch(SEND_NOTIFICATION_PATH, MagicMock())
    @patch("extensions.authorization.callbacks.callbacks.send_user_off_board_push")
    def test_success_link_unlink_proxy(self, notification: MagicMock):
        # link proxy to user
        user_id = USER_ID_WITHOUT_PROXY
        data = {LinkProxyRequestObject.PROXY_EMAIL: "test+user+proxy2@test.com"}
        url = f"{self.base_route}/{user_id}/assign-proxy"
        headers = self.get_headers_for_token(user_id)
        rsp = self.post(url, data, headers)
        self.assertEqual(201, rsp.status_code)

        notification.assert_not_called()
        # checked proxy was assigned
        proxy = self.mongo_database.user.find_one(
            {f"{User.ROLES}.{RoleAssignment.RESOURCE}": f"user/{user_id}"}
        )
        self.assertIsNotNone(proxy)
        self.assertEqual(data[LinkProxyRequestObject.PROXY_EMAIL], proxy["email"])

        # unlink proxy from user
        data = {UnlinkProxyRequestObject.PROXY_ID: str(proxy[User.ID_])}
        url = f"{self.base_route}/{user_id}/unassign-proxy"
        rsp = self.post(url, data, headers)
        self.assertEqual(204, rsp.status_code)
        notification.assert_called_once()

    def test_failure_link_proxy_no_request_body(self):
        url = f"{self.base_route}/{USER_ID_WITHOUT_PROXY}/assign-proxy"
        headers = self.get_headers_for_token(USER_ID_WITHOUT_PROXY)
        rsp = self.post(url, None, headers)
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(ErrorCodes.INVALID_REQUEST, rsp.json["code"])

    @patch(SEND_NOTIFICATION_PATH, MagicMock())
    def test_success_reactivate_proxy_after_assigned_to_active_user(self):
        user_id = "5e8f0c74b50aa9656c34779c"
        data = {LinkProxyRequestObject.PROXY_EMAIL: "test+user+proxy3@test.com"}
        url = f"{self.base_route}/{user_id}/assign-proxy"
        headers = self.get_headers_for_token(user_id)
        rsp = self.post(url, data, headers)
        self.assertEqual(201, rsp.status_code)

        proxy_headers = self.get_headers_for_token(PROXY_USER_ID)
        rsp = self.flask_client.get(
            f"{self.base_route}/{PROXY_USER_ID}/configuration",
            headers=proxy_headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertFalse(rsp.json["isOffBoarded"])

    @patch(SEND_NOTIFICATION_PATH, MagicMock())
    def test_success_reactivate_proxy_after_assigned_user_is_reactivated(self):
        user_id = "5e8f0c74b50aa9656c34789e"
        proxy_user_id = "6192061841fee21a727f8aaa"
        self.reactivate_user(user_id)
        proxy_headers = self.get_headers_for_token(proxy_user_id)
        rsp = self.flask_client.get(
            f"{self.base_route}/{proxy_user_id}/configuration",
            headers=proxy_headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertFalse(rsp.json["isOffBoarded"])

    def reactivate_user(self, user_id: str):
        reactivate_path = f"{self.base_route}/{user_id}/reactivate"
        rsp = self.flask_client.post(
            reactivate_path, headers=self.get_headers_for_token(VALID_CONTRIBUTOR_ID)
        )
        self.assertEqual(rsp.status_code, 200)
