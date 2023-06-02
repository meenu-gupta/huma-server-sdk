from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

from werkzeug.local import LocalStack

from extensions.authorization.models.user import User

from extensions.identity_verification.router.identity_verification_requests import (
    GenerateIdentityVerificationTokenRequestObject,
    CreateVerificationLogRequestObject,
)
from extensions.identity_verification.use_cases.create_user_verification_log_use_case import (
    CreateVerificationLogUseCase,
)
from extensions.identity_verification.use_cases.generate_identity_verification_sdk_token_use_case import (
    GenerateIdentityVerificationSdkTokenUseCase,
)
from extensions.module_result.exceptions import InvalidModuleConfiguration
from sdk.common.exceptions.exceptions import BundleIdMissingException
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.di.components import read_config
from .test_helpers import (
    get_sample_user_dict,
    get_sample_verification_sdk_token_request,
    get_sample_create_user_verification_log_request_dict,
    get_sample_deployment,
)

SDK_CONFIG_PATH = Path(__file__).with_name("config.test.yaml")

USE_CASE_PATH = "extensions.identity_verification.use_cases.generate_identity_verification_sdk_token_use_case"
LOG_USE_CASE_PATH = (
    "extensions.identity_verification.use_cases.create_user_verification_log_use_case"
)


class MockAuthService(MagicMock):
    retrieve_user_profile = MagicMock()
    retrieve_user_profile.return_value = User.from_dict(get_sample_user_dict())
    update_user_profile = MagicMock()


class MockAuthServiceWithApplicantId(MagicMock):
    retrieve_user_profile = MagicMock()
    retrieve_user_profile.return_value = User.from_dict(
        {
            **get_sample_user_dict(),
            User.ONFIDO_APPLICANT_ID: "8a94ba54-161b-49ab-8c76-f0b56de3a414",
        }
    )
    update_user_profile = MagicMock()


class MockOnfidoAdapter(MagicMock):
    create_applicant = MagicMock()
    create_applicant.return_value = "4a25e22e-4098-4f3e-b666-eaf78c019c52"
    generate_sdk_token = MagicMock()
    generate_sdk_token.return_value = "token"
    create_check = MagicMock()


class MockDeploymentRepo(MagicMock):
    retrieve_deployment = MagicMock()
    retrieve_deployment.return_value = get_sample_deployment()


class MockUserVerificationRepo(MagicMock):
    create_or_update_verification_log = MagicMock()


class IdentityVerificationTests(TestCase):
    phoenix_config: PhoenixServerConfig

    @classmethod
    def setUpClass(cls) -> None:
        cls.phoenix_config: PhoenixServerConfig = read_config(str(SDK_CONFIG_PATH))

    @patch(f"{USE_CASE_PATH}.AuthorizationService", MockAuthService)
    def test_success_generate_identity_verification_sdk_token(self):
        use_case = GenerateIdentityVerificationSdkTokenUseCase(
            config=self.phoenix_config,
            adapter=MockOnfidoAdapter(),
            deployment_repo=MockDeploymentRepo(),
        )
        request_object = GenerateIdentityVerificationTokenRequestObject.from_dict(
            get_sample_verification_sdk_token_request()
        )

        use_case.execute(request_object)

        MockOnfidoAdapter().generate_sdk_token.assert_called_once()
        MockOnfidoAdapter().create_applicant.assert_called_once()

    @patch(f"{USE_CASE_PATH}.AuthorizationService", MockAuthService)
    def test_failure_generate_sdk_token_with_missing_first_name(self):
        use_case = GenerateIdentityVerificationSdkTokenUseCase(
            config=self.phoenix_config,
            adapter=MockOnfidoAdapter(),
            deployment_repo=MockDeploymentRepo(),
        )
        body = get_sample_verification_sdk_token_request()
        body.pop(GenerateIdentityVerificationTokenRequestObject.LEGAL_FIRST_NAME)

        request_object = GenerateIdentityVerificationTokenRequestObject.from_dict(body)
        with self.assertRaises(ConvertibleClassValidationError):
            use_case.execute(request_object)

    def test_failure_generate_sdk_token_with_missing_application_id(self):
        request_dict = get_sample_verification_sdk_token_request()
        request_dict.pop(GenerateIdentityVerificationTokenRequestObject.APPLICATION_ID)
        with self.assertRaises(BundleIdMissingException):
            GenerateIdentityVerificationTokenRequestObject.from_dict(request_dict)

    def test_failure_create_verification_log_with_verification_result(self):
        request_dict = get_sample_create_user_verification_log_request_dict()
        request_dict[CreateVerificationLogRequestObject.VERIFICATION_RESULT] = "CLEAR"
        with self.assertRaises(ConvertibleClassValidationError):
            CreateVerificationLogRequestObject.from_dict(request_dict)

    @patch(f"{LOG_USE_CASE_PATH}.AuthorizationService", MockAuthServiceWithApplicantId)
    @patch(f"{LOG_USE_CASE_PATH}.g", LocalStack())
    def test_success_create_identity_verification_log(self):
        use_case = CreateVerificationLogUseCase(
            config=self.phoenix_config,
            adapter=MockOnfidoAdapter(),
            deployment_repo=MockDeploymentRepo(),
            verification_log_repo=MockUserVerificationRepo(),
        )
        request_object = CreateVerificationLogRequestObject.from_dict(
            get_sample_create_user_verification_log_request_dict()
        )

        use_case.execute(request_object)

        MockUserVerificationRepo().create_or_update_verification_log.assert_called_once()
        MockOnfidoAdapter().create_check.assert_called_once()
