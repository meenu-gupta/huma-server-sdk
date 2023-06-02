from pathlib import Path
from unittest.mock import patch

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.user import User
from extensions.authorization.router.user_profile_request import (
    LinkProxyRequestObject,
    UnlinkProxyRequestObject,
)
from extensions.deployment.boarding.econsent_module import EConsentModule
from extensions.deployment.component import DeploymentComponent
from extensions.exceptions import RoleErrorCodes
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.models.primitives import Weight
from extensions.organization.component import OrganizationComponent
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    now_str,
    TEST_FILE_PATH,
)
from extensions.tests.shared.test_helpers import simple_econsent_log
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.storage.component import StorageComponent
from sdk.versioning.component import VersionComponent

DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
PARTICIPANT_ID = "5ed803dd5f2f99da73684412"
PROXY_USER_ID = "5e8f0c74b50aa9656c34789c"
PARTICIPANT_EMAIL = "user@test.com"
PROXY_EMAIL = "proxy@huma.com"
OTHER_DEPLOYMENT_ID = "5d386cc6ff885918d96eda4c"
SINGLE_PARTICIPANT_ID = "5e8f0c74b50aa9656c34789b"
SINGLE_PARTICIPANT_EMAIL = "user2@test.com"
LATEST_ECONSENT = "5e9443789911c97c0b639444"


class ProxyPermissionTestCase(ExtensionTestCase):
    override_config = {"server.moduleResult.enableAuthz": "true"}

    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        StorageComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]

    fixtures = [Path(__file__).parent.joinpath("fixtures/roles_dump.json")]
    base_route = "api/extensions/v1beta/user"

    @staticmethod
    def sample_weight(value=100):
        return {
            Weight.DEPLOYMENT_ID: DEPLOYMENT_ID,
            Weight.VERSION: 0,
            Weight.DEVICE_NAME: "iOS",
            Weight.IS_AGGREGATED: False,
            Weight.START_DATE_TIME: now_str(),
            Weight.VALUE: value,
            "type": Weight.__name__,
        }

    @patch("extensions.deployment.tasks.update_econsent_pdf_location.delay")
    def _sign_econsent_by_user(self, mock_async_task):
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{PARTICIPANT_ID}/econsent/{LATEST_ECONSENT}/sign",
            headers=self.get_headers_for_token(PARTICIPANT_ID),
            json=simple_econsent_log(),
        )
        self.assertEqual(201, rsp.status_code)

    def test_success_retrieve_participant_profile(self):
        headers = self.get_headers_for_token(PROXY_USER_ID)
        url = f"{self.base_route}/{PARTICIPANT_ID}"
        rsp = self.flask_client.get(url, headers=headers)
        self.assertEqual(200, rsp.status_code)
        self.assertIn(User.FAMILY_NAME, rsp.json)
        self.assertIn(User.EMAIL, rsp.json)
        self.assertIn(User.GIVEN_NAME, rsp.json)
        self.assertEqual(PARTICIPANT_EMAIL, rsp.json[User.EMAIL])

    def test_success_retrieve_proxy_profile(self):
        self._sign_econsent_by_user()
        headers = self.get_headers_for_token(PARTICIPANT_ID)
        url = f"{self.base_route}/{PROXY_USER_ID}"
        rsp = self.flask_client.get(url, headers=headers)
        self.assertEqual(200, rsp.status_code)
        self.assertIn(User.FAMILY_NAME, rsp.json)
        self.assertIn(User.EMAIL, rsp.json)
        self.assertIn(User.GIVEN_NAME, rsp.json)
        self.assertEqual(PROXY_EMAIL, rsp.json[User.EMAIL])

    def test_success_update_participant_profile(self):
        headers = self.get_headers_for_token(PROXY_USER_ID)
        url = f"{self.base_route}/{PARTICIPANT_ID}"
        body = {User.TIMEZONE: "Europe/Kiev"}
        rsp = self.flask_client.post(url, headers=headers, json=body)
        self.assertEqual(200, rsp.status_code)

    def test_success_submit_module_result_for_participant(self):
        headers = self.get_headers_for_token(PROXY_USER_ID)
        url = f"{self.base_route}/{PARTICIPANT_ID}/module-result/Weight"
        body = [self.sample_weight()]
        rsp = self.flask_client.post(url, headers=headers, json=body)
        self.assertEqual(201, rsp.status_code)

    def test_success_retrieve_participant_module_result(self):
        headers = self.get_headers_for_token(PROXY_USER_ID)
        url = f"{self.base_route}/{PARTICIPANT_ID}/module-result/Weight/search"
        rsp = self.flask_client.post(url, headers=headers)
        self.assertEqual(200, rsp.status_code)

    def test_failure_submit_module_result_for_other_deployment(self):
        headers = self.get_headers_for_token(PROXY_USER_ID)
        url = f"{self.base_route}/{PARTICIPANT_ID}/module-result/Weight"
        body = self.sample_weight()
        body[Weight.DEPLOYMENT_ID] = OTHER_DEPLOYMENT_ID
        rsp = self.flask_client.post(url, headers=headers, json=body)
        self.assertEqual(403, rsp.status_code)

    def test_success_upload_personal_documents_by_proxy(self):
        filename = f"user/{PARTICIPANT_ID}/PersonalDocuments/"
        with open(TEST_FILE_PATH, "rb") as file:
            data = {
                "filename": filename,
                "mime": "application/octet-stream",
                "file": file,
            }
            rsp = self.flask_client.post(
                f"/api/storage/v1beta/upload/{self.config.server.storage.defaultBucket}",
                data=data,
                headers=self.get_headers_for_token(PROXY_USER_ID),
                content_type="multipart/form-data",
            )
            self.assertEqual(201, rsp.status_code)

    def test_failure_link_not_proxy(self):
        self._sign_econsent_by_user()
        headers = self.get_headers_for_token(PARTICIPANT_ID)
        url = f"{self.base_route}/{PARTICIPANT_ID}/assign-proxy"
        link_data = {LinkProxyRequestObject.PROXY_EMAIL: SINGLE_PARTICIPANT_EMAIL}
        rsp = self.flask_client.post(url, headers=headers, json=link_data)
        self.assertEqual(403, rsp.status_code)

    def test_failure_link_already_linked_proxy(self):
        headers = self.get_headers_for_token(SINGLE_PARTICIPANT_ID)
        url = f"{self.base_route}/{SINGLE_PARTICIPANT_ID}/assign-proxy"
        link_data = {LinkProxyRequestObject.PROXY_EMAIL: PROXY_EMAIL}
        rsp = self.flask_client.post(url, headers=headers, json=link_data)
        self.assertEqual(400, rsp.status_code)

    def test_failure_link_participant_with_proxy(self):
        headers = self.get_headers_for_token(PARTICIPANT_ID)
        url = f"{self.base_route}/{PARTICIPANT_ID}/assign-proxy"
        link_data = {LinkProxyRequestObject.PROXY_EMAIL: PROXY_EMAIL}
        rsp = self.flask_client.post(url, headers=headers, json=link_data)
        self.assertEqual(400, rsp.status_code)

    def test_failure_link_to_own_email(self):
        headers = self.get_headers_for_token(SINGLE_PARTICIPANT_ID)
        url = f"{self.base_route}/{SINGLE_PARTICIPANT_ID}/assign-proxy"
        link_data = {LinkProxyRequestObject.PROXY_EMAIL: SINGLE_PARTICIPANT_EMAIL}
        rsp = self.flask_client.post(url, headers=headers, json=link_data)
        self.assertEqual(403, rsp.status_code)

    def test_proxy_can_reach_linked_user_econsent(self):
        self._sign_econsent_by_user()

        url = f"{self.base_route}/{PARTICIPANT_ID}/econsent/{LATEST_ECONSENT}/pdf"
        rsp = self.flask_client.get(
            url, headers=self.get_headers_for_token(PROXY_USER_ID)
        )
        self.assertEqual(200, rsp.status_code)

    @patch.object(
        EConsentModule, "validate_if_allowed_to_reach_route", lambda a, b, c: False
    )
    def test_proxy_gets_unlinked_exception_when_not_linked(self):
        headers = self.get_headers_for_token(PARTICIPANT_ID)
        url = f"{self.base_route}/{PARTICIPANT_ID}/unassign-proxy"
        unlink_data = {UnlinkProxyRequestObject.PROXY_ID: PROXY_USER_ID}
        rsp = self.flask_client.post(url, headers=headers, json=unlink_data)
        self.assertEqual(204, rsp.status_code)

        proxy_headers = self.get_headers_for_token(PROXY_USER_ID)
        submit_url = f"{self.base_route}/{PARTICIPANT_ID}/module-result/Weight"
        body = [self.sample_weight()]
        rsp = self.flask_client.post(submit_url, headers=proxy_headers, json=body)
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(RoleErrorCodes.PROXY_UNLINKED, rsp.json["code"])
