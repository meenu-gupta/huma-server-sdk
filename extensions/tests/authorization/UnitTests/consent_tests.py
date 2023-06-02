from unittest import TestCase
from unittest.mock import MagicMock, patch

from extensions.authorization.use_cases.sign_consent_use_case import SignConsentUseCase
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.router.deployment_requests import SignConsentRequestObject
from extensions.tests.authorization.UnitTests.test_helpers import (
    get_sample_consent,
    get_sample_sign_consent_request,
)
from sdk.common.exceptions.exceptions import ConsentNotAgreedException
from sdk.common.utils.convertible import ConvertibleClassValidationError

USE_CASE_PATH = "extensions.authorization.use_cases.sign_consent_use_case"


class MockConsentRepo(MagicMock):
    create_consent_log = MagicMock()


class MockService:
    def __init__(self, *args, **kwargs):
        pass

    def retrieve_deployment(self, deployment_id: str):
        return Deployment(consent=Consent.from_dict(get_sample_consent()))


class MockServiceNoAgreement(MockService):
    def retrieve_deployment(self, deployment_id: str):
        consent_dict = get_sample_consent()
        consent_dict[Consent.SECTIONS] = []
        return Deployment(consent=Consent.from_dict(consent_dict))


class ConsentTests(TestCase):
    def setUp(self) -> None:
        MockConsentRepo.create_consent_log.reset_mock()

    @patch(f"{USE_CASE_PATH}.DeploymentService", MockService)
    def test_success_create_consent_log(self):
        use_case = SignConsentUseCase(MockConsentRepo())
        request_object = SignConsentRequestObject.from_dict(
            get_sample_sign_consent_request()
        )
        use_case.execute(request_object)
        MockConsentRepo.create_consent_log.assert_called_once()

    @patch(f"{USE_CASE_PATH}.DeploymentService", MockService)
    def test_failure_create_consent_log_with_no_agreement(self):
        use_case = SignConsentUseCase(MockConsentRepo())
        consent_request = get_sample_sign_consent_request()
        consent_request.pop(ConsentLog.AGREEMENT)
        request_object = SignConsentRequestObject.from_dict(consent_request)
        with self.assertRaises(ConsentNotAgreedException):
            use_case.execute(request_object)

    @patch(f"{USE_CASE_PATH}.DeploymentService", MockServiceNoAgreement)
    def test_success_create_consent_log_with_consent_with_no_agreement_section(self):
        use_case = SignConsentUseCase(MockConsentRepo())
        consent_request = get_sample_sign_consent_request()
        consent_request.pop(ConsentLog.AGREEMENT)
        request_object = SignConsentRequestObject.from_dict(consent_request)
        use_case.execute(request_object)
        MockConsentRepo.create_consent_log.assert_called_once()

    def test_failure_request_object_with_revision(self):
        consent_request = get_sample_sign_consent_request()
        consent_request[ConsentLog.REVISION] = 1
        consent_request.pop(ConsentLog.AGREEMENT)
        with self.assertRaises(ConvertibleClassValidationError):
            SignConsentRequestObject.from_dict(consent_request)

    def test_failure_request_object_with_no_consent_id(self):
        consent_request = get_sample_sign_consent_request()
        consent_request.pop(ConsentLog.CONSENT_ID)
        with self.assertRaises(ConvertibleClassValidationError):
            SignConsentRequestObject.from_dict(consent_request)
