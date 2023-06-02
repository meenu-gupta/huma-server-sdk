import copy
from pathlib import Path
from unittest.mock import patch, MagicMock

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.user import User
from extensions.authorization.repository.mongo_user_repository import (
    MongoUserRepository,
)
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.exceptions import DeploymentErrorCodes
from extensions.identity_verification.component import IdentityVerificationComponent
from extensions.identity_verification.models.identity_verification import (
    IdentityVerificationAction,
)
from extensions.identity_verification.models.identity_verification_log import (
    VerificationLog,
    Document,
)
from extensions.identity_verification.models.identity_verification_sdk_token_response import (
    IdentityVerificationSdkTokenResponse,
)
from extensions.identity_verification.repository.mongo_verification_log_repository import (
    MongoVerificationLogRepository,
)
from extensions.identity_verification.router.identity_verification_requests import (
    GenerateIdentityVerificationTokenRequestObject,
)
from extensions.identity_verification.router.identity_verification_requests import (
    OnfidoVerificationResult,
)
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.identity_verification.IntegrationTests.test_helpers import (
    get_sample_create_user_verification_log_request_dict,
    get_sample_create_user_verification_log_request_dict_required_docs_in_deployment,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.audit_logger.component import AuditLoggerComponent
from sdk.audit_logger.repo.mongo_audit_log_repository import MongoAuditLogRepository
from sdk.auth.component import AuthComponent
from sdk.common.adapter.identity_verification_adapter import IdentityVerificationAdapter
from sdk.common.adapter.identity_verification_mail_adapter import (
    IdentityVerificationEmailAdapter,
)
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.common.utils.sensitive_data import MASK
from sdk.phoenix.audit_logger import AuditLog

USER_ID_WITHOUT_APPLICANT_ID = "5e8f0c74b50aa9656c34789c"
USER_ID_WITH_APPLICANT_ID = "5e8f0c74b50aa9656c34789d"

PATH_G = "extensions.identity_verification.router.identity_verification_router.g"
USE_CASE_PATH = "extensions.identity_verification.use_cases.generate_identity_verification_sdk_token_use_case.GenerateIdentityVerificationSdkTokenUseCase"
VALID_USER_ID = "5e8f0c74b50aa9656c34789d"
APPLICANT_ID = "8a94ba54-161b-49ab-8c76-f0b56de3a414"

ONFIDO_RESULT_USER_CASE = (
    "extensions.identity_verification.use_cases.receive_onfido_result_use_case"
)
ONFIDO_SIGNATURE_PATH = "extensions.identity_verification.router.identity_verification_public_router.check_onfido_signature"

ONFIDO_VERIFICATION_RESULT_SAMPLE = {
    "id": "26411331-15e2-4a11-9ba0-b135d4131902",
    "created_at": "2021-02-24T20:57:56Z",
    "status": "complete",
    "redirect_uri": None,
    "result": "clear",
    "sandbox": True,
    "tags": [],
    "results_uri": "https://dashboard.onfido.com/checks/26411331-15e2-4a11-9ba0-b135d4131902",
    "form_uri": None,
    "paused": False,
    "version": "3.0",
    "report_ids": ["93bb36ee-6c7f-468a-9762-7985f4f2a0d6"],
    "href": "/v3/checks/26411331-15e2-4a11-9ba0-b135d4131902",
    "applicant_id": APPLICANT_ID,
    "applicant_provides_data": False,
}

SAMPLE_CALLBACK_PAYLOAD = {
    "payload": {
        "resource_type": "check",
        "action": "check.completed",
        "object": {
            "id": "26411331-15e2-4a11-9ba0-b135d4131902",
            "status": "complete",
            "completed_at_iso8601": "2021-02-24T20:57:58Z",
            "href": "https://api.onfido.com/v3/checks/26411331-15e2-4a11-9ba0-b135d4131902",
        },
    }
}


X_SHA2_SIGNATURE = "b52b1938e333f5da99e8fa83742693253f4d8c7edffaeb5eb3962042215d98bf"


class MockBundle:
    instance = MagicMock()
    bundle_id = "com.huma.HumaApp.dev"


class MockUser:
    instance = MagicMock()
    id = USER_ID_WITHOUT_APPLICANT_ID


class MockG:
    instance = MagicMock()
    user = MockUser()
    user_agent = MockBundle()
    authz_user = MagicMock()
    authz_user.user = User(id=str(ObjectId()))
    authz_user.deployment_id = MagicMock()
    authz_user.deployment_id.return_value = "5d386cc6ff885918d96edb2c"

    def get(self, _):
        return self.user_agent


class MockOnfidoAdapter:
    instance = MagicMock()
    webhook_token = "XVRHewzwVo8p8z8NZXq-ISWH3aNHUQI-"
    retrieve_verification_check = MagicMock()


class MockEmailAdapter:
    instance = MagicMock()
    send_verification_result_email = MagicMock()


class IdentityVerificationTestCase(ExtensionTestCase):
    API_URL = "/api/identity-verification/v1beta"
    PUBLIC_API_URL = "/api/identity-verification-public/v1beta"

    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        IdentityVerificationComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        AuditLoggerComponent(),
    ]

    fixtures = [Path(__file__).parent.joinpath("fixtures/deployment_dump.json")]
    override_config = {
        "server.adapters.onfido.webhookToken": "XVRHewzwVo8p8z8NZXq-ISWH3aNHUQI-",
        "server.deployment.onBoarding": "true",
        "server.deployment.offBoarding": "true",
    }

    def setUp(self):
        def bind_adapters(binder):
            binder.bind_to_provider(
                IdentityVerificationAdapter, lambda: MockOnfidoAdapter()
            )
            binder.bind_to_provider(
                IdentityVerificationEmailAdapter, lambda: MockEmailAdapter()
            )

        super().setUp()
        self.headers = self.get_headers_for_token(VALID_USER_ID)
        inject.get_injector_or_die().rebind(config=bind_adapters)
        MockEmailAdapter.send_verification_result_email.reset_mock()

    def get_user(self, user_id: str):
        return self.mongo_database["user"].find_one({User.ID_: ObjectId(user_id)})

    @patch(PATH_G, MockG())
    @patch(f"{USE_CASE_PATH}._create_or_get_applicant_id")
    @patch("sdk.common.adapter.onfido.onfido_adapter.OnfidoAdapter.generate_sdk_token")
    def test_success_generate_onfido_sdk_token(
        self, mock_create_applicant, mock_generate_token
    ):
        mock_create_applicant.return_value = "4a25e22e-4098-4f3e-b666-eaf78c019c52"
        mock_generate_token.return_value = "sdk token"
        body = {
            GenerateIdentityVerificationTokenRequestObject.LEGAL_FIRST_NAME: "Test",
            GenerateIdentityVerificationTokenRequestObject.LEGAL_LAST_NAME: "Test",
        }
        rsp = self.flask_client.post(
            f"{self.API_URL}/generate-identity-verification-sdk-token",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        self.assertIn(IdentityVerificationSdkTokenResponse.APPLICANT_ID, rsp.json)
        self.assertIn(IdentityVerificationSdkTokenResponse.TOKEN, rsp.json)
        self.assertIn(
            IdentityVerificationSdkTokenResponse.UTC_EXPIRATION_DATE_TIME, rsp.json
        )

    @patch(PATH_G, MockG())
    @patch(f"{USE_CASE_PATH}._create_or_get_applicant_id")
    @patch("sdk.common.adapter.onfido.onfido_adapter.OnfidoAdapter.generate_sdk_token")
    def test_success_generate_onfido_sdk_token_audit_log(
        self, mock_create_applicant, mock_generate_token
    ):
        mock_create_applicant.return_value = "4a25e22e-4098-4f3e-b666-eaf78c019c52"
        mock_generate_token.return_value = "sdk token"
        body = {
            GenerateIdentityVerificationTokenRequestObject.LEGAL_FIRST_NAME: "Test",
            GenerateIdentityVerificationTokenRequestObject.LEGAL_LAST_NAME: "Test",
        }
        rsp = self.flask_client.post(
            f"{self.API_URL}/generate-identity-verification-sdk-token",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        query = {
            AuditLog.ACTION: IdentityVerificationAction.GenerateIdentityVerificationToken.value
        }
        log = self.mongo_database[
            MongoAuditLogRepository.AUDIT_LOG_COLLECTION
        ].find_one(query)
        self.assertIsNotNone(log)
        self.assertEqual(log[AuditLog.REQUEST_OBJECT], body)
        self.assertEqual(
            log[AuditLog.RESPONSE_OBJECT][IdentityVerificationSdkTokenResponse.TOKEN],
            MASK,
        )

    @patch("sdk.common.adapter.onfido.onfido_adapter.OnfidoAdapter.create_check")
    def test_success_create_verification_log_required_docs_config_in_onboarding_configs(
        self, mock_create_check
    ):
        mock_create_check.return_value = True
        body = get_sample_create_user_verification_log_request_dict()
        headers = self.get_headers_for_token(USER_ID_WITH_APPLICANT_ID)
        rsp = self.flask_client.post(
            f"{self.API_URL}/user-verification-log",
            json=body,
            headers=headers,
        )
        self.assertEqual(201, rsp.status_code)
        user = self.get_user(USER_ID_WITH_APPLICANT_ID)
        expected_status = User.VerificationStatus.ID_VERIFICATION_IN_PROCESS.value
        self.assertEqual(expected_status, user[User.VERIFICATION_STATUS])

    @patch("sdk.common.adapter.onfido.onfido_adapter.OnfidoAdapter.create_check")
    def test_success_create_verification_log_required_docs_config_in_deployment(
        self, mock_create_check
    ):
        mock_create_check.return_value = True
        body = (
            get_sample_create_user_verification_log_request_dict_required_docs_in_deployment()
        )
        headers = self.get_headers_for_token("60d321da171c272686488b8c")
        rsp = self.flask_client.post(
            f"{self.API_URL}/user-verification-log",
            json=body,
            headers=headers,
        )
        self.assertEqual(201, rsp.status_code)
        user = self.get_user("60d321da171c272686488b8c")
        expected_status = User.VerificationStatus.ID_VERIFICATION_IN_PROCESS.value
        self.assertEqual(expected_status, user[User.VERIFICATION_STATUS])

    @patch("sdk.common.adapter.onfido.onfido_adapter.OnfidoAdapter.create_check")
    def test_success_update_verification_log(self, mock_create_check):
        mock_create_check.return_value = True

        def create_verification_log():
            body = get_sample_create_user_verification_log_request_dict()
            headers = self.get_headers_for_token(USER_ID_WITH_APPLICANT_ID)
            rsp = self.flask_client.post(
                f"{self.API_URL}/user-verification-log",
                json=body,
                headers=headers,
            )
            self.assertEqual(201, rsp.status_code)

        for i in range(3):
            create_verification_log()

        logs = self.mongo_database[
            MongoVerificationLogRepository.VERIFICATION_LOG_COLLECTION
        ].find_one({VerificationLog.USER_ID: ObjectId(USER_ID_WITH_APPLICANT_ID)})

        for document in logs[VerificationLog.DOCUMENTS]:
            self.assertIsNotNone(document[Document.ID])
            self.assertIsNotNone(document[Document.IS_ACTIVE])

    @patch("sdk.common.push_notifications.push_notifications_utils.NotificationService")
    def test_success_set_onfido_results_verification_succeed(
        self, notification_service
    ):
        headers = {"X-SHA2-Signature": X_SHA2_SIGNATURE}
        payload = SAMPLE_CALLBACK_PAYLOAD
        ONFIDO_VERIFICATION_RESULT_SAMPLE[
            OnfidoVerificationResult.STATUS
        ] = VerificationLog.StatusType.COMPLETE.value

        ONFIDO_VERIFICATION_RESULT_SAMPLE[
            OnfidoVerificationResult.RESULT
        ] = VerificationLog.ResultType.CLEAR.value

        MockOnfidoAdapter.retrieve_verification_check.return_value = (
            ONFIDO_VERIFICATION_RESULT_SAMPLE
        )

        rsp = self.flask_client.post(
            f"{self.PUBLIC_API_URL}/receive-onfido-result",
            headers=headers,
            json=payload,
        )
        self.assertEqual(rsp.status_code, 200)

        notification_service().push_for_user.assert_called_once()

        MockEmailAdapter.send_verification_result_email.assert_called_once_with(
            to="user+2@user.com", username="user2 user2", locale=Language.EN
        )

        res = self.mongo_database[MongoUserRepository.USER_COLLECTION].find_one(
            {User.ID_: ObjectId(VALID_USER_ID)}
        )
        self.assertEqual(
            res[User.VERIFICATION_STATUS],
            User.VerificationStatus.ID_VERIFICATION_SUCCEEDED.value,
        )

    @patch("sdk.common.push_notifications.push_notifications_utils.NotificationService")
    def test_success_set_onfido_results_verification_in_progress(
        self, notification_service
    ):
        headers = {"X-SHA2-Signature": X_SHA2_SIGNATURE}
        payload = SAMPLE_CALLBACK_PAYLOAD

        ONFIDO_VERIFICATION_RESULT_SAMPLE[
            OnfidoVerificationResult.STATUS
        ] = VerificationLog.StatusType.AWAITING_APPROVAL.value

        ONFIDO_VERIFICATION_RESULT_SAMPLE[
            OnfidoVerificationResult.RESULT
        ] = VerificationLog.ResultType.CLEAR.value

        MockOnfidoAdapter.retrieve_verification_check.return_value = (
            ONFIDO_VERIFICATION_RESULT_SAMPLE
        )

        rsp = self.flask_client.post(
            f"{self.PUBLIC_API_URL}/receive-onfido-result",
            headers=headers,
            json=payload,
        )
        self.assertEqual(rsp.status_code, 200)

        notification_service().push_for_user.assert_not_called()
        MockEmailAdapter.send_verification_result_email.assert_not_called()

        res = self.mongo_database[MongoUserRepository.USER_COLLECTION].find_one(
            {User.ID_: ObjectId(VALID_USER_ID)}
        )
        self.assertEqual(
            res[User.VERIFICATION_STATUS],
            User.VerificationStatus.ID_VERIFICATION_IN_PROCESS.value,
        )

        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/primitive/primitive_type/{VALID_USER_ID}",
            headers=self.headers,
        )
        self.assertEqual(428, rsp.status_code)

    @patch("sdk.common.push_notifications.push_notifications_utils.NotificationService")
    def test_success_set_onfido_results_verification_failed(self, notification_service):
        headers = {"X-SHA2-Signature": X_SHA2_SIGNATURE}
        payload = SAMPLE_CALLBACK_PAYLOAD

        ONFIDO_VERIFICATION_RESULT_SAMPLE[
            OnfidoVerificationResult.STATUS
        ] = VerificationLog.StatusType.COMPLETE.value

        ONFIDO_VERIFICATION_RESULT_SAMPLE[
            OnfidoVerificationResult.RESULT
        ] = VerificationLog.ResultType.CONSIDER.value

        MockOnfidoAdapter.retrieve_verification_check.return_value = (
            ONFIDO_VERIFICATION_RESULT_SAMPLE
        )

        rsp = self.flask_client.post(
            f"{self.PUBLIC_API_URL}/receive-onfido-result",
            headers=headers,
            json=payload,
        )
        self.assertEqual(rsp.status_code, 200)
        notification_service().push_for_user.assert_called_once()
        MockEmailAdapter.send_verification_result_email.assert_called_once_with(
            to="user+2@user.com", username="user2 user2", locale=Language.EN
        )

        res = self.mongo_database[MongoUserRepository.USER_COLLECTION].find_one(
            {User.ID_: ObjectId(VALID_USER_ID)}
        )
        self.assertEqual(
            res[User.VERIFICATION_STATUS],
            User.VerificationStatus.ID_VERIFICATION_FAILED.value,
        )

        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/Weight",
            headers=self.headers,
        )
        self.assertEqual(412, rsp.status_code)
        self.assertEqual(
            rsp.json["code"],
            DeploymentErrorCodes.OFF_BOARDING_USER_FAIL_ID_VERIFICATION,
        )

    def test_onfido_wrong_token(self):
        headers = {"X-SHA2-Signature": "kkkk"}
        payload = SAMPLE_CALLBACK_PAYLOAD
        rsp = self.flask_client.post(
            f"{self.PUBLIC_API_URL}/receive-onfido-result",
            headers=headers,
            json=payload,
        )
        self.assertEqual(rsp.status_code, 500)

    @patch(f"{ONFIDO_RESULT_USER_CASE}.prepare_and_send_push_notification")
    @patch(ONFIDO_SIGNATURE_PATH)
    def test_success_recieve_onfido_result(self, _, notification_mock):
        headers = {"X-SHA2-Signature": X_SHA2_SIGNATURE}
        payload = SAMPLE_CALLBACK_PAYLOAD
        sample_payload = copy.deepcopy(ONFIDO_VERIFICATION_RESULT_SAMPLE)
        sample_payload["applicant_id"] = "not existing id"

        sample_payload[
            OnfidoVerificationResult.STATUS
        ] = VerificationLog.StatusType.AWAITING_APPROVAL.value

        sample_payload[
            OnfidoVerificationResult.RESULT
        ] = VerificationLog.ResultType.CLEAR.value

        MockOnfidoAdapter.retrieve_verification_check.return_value = sample_payload

        rsp = self.flask_client.post(
            f"{self.PUBLIC_API_URL}/receive-onfido-result",
            headers=headers,
            json=payload,
        )
        self.assertEqual(rsp.status_code, 200)
