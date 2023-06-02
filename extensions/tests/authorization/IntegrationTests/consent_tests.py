from pathlib import Path

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.shared.test_helpers import consent_log, simple_consent
from sdk.auth.component import AuthComponent
from sdk.tests.application_test_utils.test_utils import IntegrationTestCase

CONFIG_PATH = Path(__file__).with_name("config.consent.test.yaml")


class BaseConsentPermissionTestCase(IntegrationTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
    ]
    config_file_path = CONFIG_PATH
    fixtures = [Path(__file__).parent.joinpath("fixtures/consent_dump.json")]

    def setUp(self) -> None:
        super().setUp()

        self.deployment_id = "5d386cc6ff885918d96edb2c"
        self.consent_id = "5e9443789911c97c0b639374"
        self.user_id = "5e8f0c74b50aa9656c34789c"
        self.super_admin_id = "5e8f0c74b50aa9656c34789b"

        self.user_headers = self.get_headers_for_token(self.user_id)
        self.super_admin_headers = self.get_headers_for_token(self.super_admin_id)


class ConsentNotSignedTestCase(BaseConsentPermissionTestCase):
    def test_consent_needed(self):
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{self.user_id}/configuration",
            headers=self.user_headers,
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertTrue(rsp.json["consentNeeded"])

    def test_success_call_profile_endpoint_before_consent_signed(self):
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{self.user_id}",
            headers=self.user_headers,
        )
        self.assertEqual(rsp.status_code, 200)


class ConsentSignedTestCase(BaseConsentPermissionTestCase):
    def setUp(self) -> None:
        super(ConsentSignedTestCase, self).setUp()

    def test_consent_needed(self):
        self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}/consent/{self.consent_id}/sign",
            json=consent_log(),
            headers=self.user_headers,
        )
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{self.user_id}/configuration",
            headers=self.user_headers,
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertFalse(rsp.json["consentNeeded"])

    def test_consent_signed_with_extra_answers(self):
        consent_log_data = consent_log()
        additional_answers = {
            "isDataSharedForFutureStudies": True,
            "isDataSharedForResearch": True,
        }
        consent_log_data[ConsentLog.ADDITIONAL_CONSENT_ANSWERS] = additional_answers
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}/consent/{self.consent_id}/sign",
            json=consent_log_data,
            headers=self.user_headers,
        )
        self.assertEqual(rsp.status_code, 201)
        log_id = rsp.json[ConsentLog.ID]
        query = {ConsentLog.ID_: ObjectId(log_id)}
        log = self.mongo_database["consentlog"].find_one(query)
        self.assertEqual(additional_answers, log[ConsentLog.ADDITIONAL_CONSENT_ANSWERS])


class NewConsentNotSignedTestCase(ConsentNotSignedTestCase):
    def setUp(self) -> None:
        super(NewConsentNotSignedTestCase, self).setUp()
        self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}/consent/{self.consent_id}/sign",
            json=consent_log(),
            headers=self.user_headers,
        )

    def test_consent_needed(self):
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/deployment/{self.deployment_id}/consent",
            json=simple_consent(),
            headers=self.super_admin_headers,
        )
        self.assertEqual(201, rsp.status_code)
        super(NewConsentNotSignedTestCase, self).test_consent_needed()


class ConsentSignTestCase(BaseConsentPermissionTestCase):
    def test_failure_consent_not_agreed(self):
        body = consent_log()
        body.pop(ConsentLog.AGREEMENT, None)
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}/consent/{self.consent_id}/sign",
            json=body,
            headers=self.user_headers,
        )
        self.assertEqual(400, rsp.status_code)

    def test_failure_sign_invalid_consent(self):
        body = consent_log()
        body.pop(ConsentLog.AGREEMENT, None)
        consent_id = "5e9443789911c97c0b639322"
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}/consent/{consent_id}/sign",
            json=body,
            headers=self.user_headers,
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300013, rsp.json["code"])


class SignConsentTestCase(BaseConsentPermissionTestCase):
    def test_failure_consent_not_agreed(self):
        body = consent_log()
        body.pop(ConsentLog.AGREEMENT, None)
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}/consent/{self.consent_id}/sign",
            json=body,
            headers=self.user_headers,
        )
        self.assertEqual(400, rsp.status_code)

    def test_failure_sign_invalid_consent(self):
        body = consent_log()
        body.pop(ConsentLog.AGREEMENT, None)
        consent_id = "5e9443789911c97c0b639322"
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}/consent/{consent_id}/sign",
            json=body,
            headers=self.user_headers,
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300013, rsp.json["code"])

    def test_success_sign_consent_with_empty_body(self) -> None:
        user_id = "5e8f0c74b50aa9656c34789d"
        consent_id = "5e9443789911c97c0b639375"
        headers = self.get_headers_for_token(user_id)
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{user_id}/consent/{consent_id}/sign",
            headers=headers,
        )
        self.assertEqual(201, rsp.status_code)
