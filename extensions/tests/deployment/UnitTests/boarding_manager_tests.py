import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from extensions.authorization.boarding.manager import BoardingManager
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment, BoardingStatus
from extensions.common.exceptions import InvalidModuleException
from extensions.deployment.boarding.consent_module import ConsentModule
from extensions.deployment.boarding.econsent_module import EConsentModule
from extensions.deployment.boarding.helper_agreement_module import HelperAgreementModule
from extensions.deployment.exceptions import OffBoardingRequiredError
from extensions.deployment.models.deployment import (
    OnboardingModuleConfig,
    Deployment,
    Features,
)
from extensions.deployment.models.status import EnableStatus
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.identity_verification.modules import IdentityVerificationModule
from extensions.module_result.boarding.az_screening_module import AZPScreeningModule
from sdk.common.utils import inject

BOARDING_MANAGER_PATH = "extensions.authorization.boarding.manager"
DEPLOYMENT_ID = "deploymentTestId"

if not inject.is_configured():
    inject.configure()


class MockDeployment:
    onboardingConfigs = [
        OnboardingModuleConfig.from_dict(
            {
                "onboardingId": "Consent",
                "status": "ENABLED",
                "configBody": {},
                "order": 2,
                "version": 1,
                "updateDateTime": "2021-03-30T06:54:26.437Z",
                "id": "6062cb22df4bfd585fcd6d47",
                "userTypes": ["User", "Proxy"],
            }
        ),
        OnboardingModuleConfig.from_dict(
            {
                "onboardingId": "IdentityVerification",
                "status": "ENABLED",
                "configBody": {},
                "order": 3,
                "version": 1,
                "updateDateTime": "2021-03-30T06:54:26.458Z",
                "id": "6062cb22df4bfd585fcd6d49",
                "userTypes": ["User"],
            }
        ),
        OnboardingModuleConfig.from_dict(
            {
                "onboardingId": "AZScreeningOnboarding",
                "status": "ENABLED",
                "configBody": {},
                "order": 4,
                "version": 1,
                "updateDateTime": "2021-03-30T06:54:26.481Z",
                "id": "6065c10f267800a450b2709a",
                "userTypes": ["User"],
            }
        ),
        OnboardingModuleConfig.from_dict(
            {
                "onboardingId": "EConsent",
                "status": "ENABLED",
                "configBody": {},
                "order": 5,
                "version": 1,
                "updateDateTime": "2021-03-30T06:54:26.481Z",
                "id": "6062cb22df4bfd585fcd6d4b",
                "userTypes": ["User"],
            }
        ),
        OnboardingModuleConfig.from_dict(
            {
                "onboardingId": "HelperAgreement",
                "status": "ENABLED",
                "configBody": {},
                "order": 1,
                "version": 1,
                "updateDateTime": "2021-03-30T06:54:26.481Z",
                "id": "606eaf75ce1736cc9d800e32",
                "userTypes": ["Proxy"],
            }
        ),
    ]


class AuthorizedUserMock(AuthorizedUser):
    is_user = MagicMock(return_value=True)
    is_proxy = MagicMock(return_value=False)
    get_consent = MagicMock(return_value={"a": "a"})
    get_econsent = MagicMock(return_value={"a": "a"})

    def __init__(self, user, deployment=None):
        self._deployment = deployment
        super(AuthorizedUserMock, self).__init__(user)

    @property
    def deployment(self):
        if self._deployment:
            return self._deployment

        configs = [
            OnboardingModuleConfig(
                onboardingId="Consent", status=EnableStatus.DISABLED
            ),
            OnboardingModuleConfig(
                onboardingId="EConsent", status=EnableStatus.DISABLED
            ),
        ]
        return Deployment(id=DEPLOYMENT_ID, onboardingConfigs=configs)


def get_authz_user(onboarded: bool = False, deployment=None):
    role = RoleAssignment.from_dict(
        {
            RoleAssignment.ROLE_ID: RoleName.USER,
            RoleAssignment.RESOURCE: f"deployment/{DEPLOYMENT_ID}",
        }
    )
    user = User(
        id="611dfe2b5f627d7d824c297a", finishedOnboarding=onboarded, roles=[role]
    )
    return AuthorizedUserMock(user, deployment)


class BoardingManagerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.deployment_repo = MagicMock()

        def bind(binder):
            binder.bind_to_provider(DeploymentRepository, cls.deployment_repo)

        inject.clear_and_configure(bind)

    def test_boarding_modules_order(self):
        authz_user = get_authz_user(deployment=MockDeployment)
        manager = BoardingManager(authz_user, "/configuration", "")
        expected_order = [
            HelperAgreementModule.name,
            ConsentModule.name,
            IdentityVerificationModule.name,
            AZPScreeningModule.name,
            EConsentModule.name,
        ]
        enabled_modules = manager._enabled_boarding_modules
        for i, module in enumerate(enabled_modules):
            if i < len(expected_order):
                self.assertEqual(expected_order[i], module.name)

    @patch(f"{BOARDING_MANAGER_PATH}.AuthorizationService")
    def test_finished_onboarding_called(self, mock_service):
        manager = BoardingManager(get_authz_user(), "/configuration", "")
        next_task = manager.get_next_onboarding_task()
        self.assertIsNone(next_task)

        mock_service().update_user_profile.assert_called_once()

    @patch(f"{BOARDING_MANAGER_PATH}.AuthorizationService")
    def test_finished_onboarding_not_called_onboarded_used(self, mock_service):
        manager = BoardingManager(get_authz_user(onboarded=True), "/configuration", "")
        next_task = manager.get_next_onboarding_task()
        self.assertIsNone(next_task)

        mock_service().update_user_profile.assert_not_called()

    @patch(f"{BOARDING_MANAGER_PATH}.ConsentModule")
    @patch(f"{BOARDING_MANAGER_PATH}.AuthorizationService")
    def test_finished_onboarding_not_called_has_task(
        self, mock_service, mock_consent_module
    ):
        mock_consent_module.is_enabled.return_value = True
        mock_consent_module.is_module_completed.return_value = False

        manager = BoardingManager(get_authz_user(), "/configuration", "")
        manager._enabled_boarding_modules = [mock_consent_module]

        next_task = manager.get_next_onboarding_task()
        self.assertIsNotNone(next_task)

        mock_service().update_user_profile.assert_not_called()

    def test_success_skip_consent_if_do_not_have_it_in_deployment(self):
        authz_user = get_authz_user(deployment=MockDeployment)
        authz_user.get_consent = MagicMock(return_value=None)
        consent_module = ConsentModule()
        consent_module.onboardingConfig = OnboardingModuleConfig.from_dict(
            {
                "onboardingId": "Consent",
                "status": "ENABLED",
                "configBody": {},
                "order": 2,
                "version": 1,
                "updateDateTime": "2021-03-30T06:54:26.437Z",
                "id": "6062cb22df4bfd585fcd6d47",
                "userTypes": ["User", "Proxy"],
            }
        )
        is_enabled = consent_module.is_enabled(authz_user)
        self.assertFalse(is_enabled)

    def test_success_skip_econsent_if_do_not_have_it_in_deployment(self):
        authz_user = get_authz_user(deployment=MockDeployment)
        authz_user.get_econsent = MagicMock(return_value=None)
        econsent_module = EConsentModule()
        econsent_module.onboardingConfig = OnboardingModuleConfig.from_dict(
            {
                "onboardingId": "EConsent",
                "status": "ENABLED",
                "configBody": {},
                "order": 5,
                "version": 1,
                "updateDateTime": "2021-03-30T06:54:26.481Z",
                "id": "6062cb22df4bfd585fcd6d4b",
                "userTypes": ["User"],
            }
        )
        is_enabled = econsent_module.is_enabled(authz_user)
        self.assertFalse(is_enabled)

    def test_failure_invalid_onboarding_id(self):
        authz_user = get_authz_user(deployment=MockDeployment)
        manager = BoardingManager(authz_user, "/configuration", "")
        with self.assertRaises(InvalidModuleException):
            manager.validate_onboarding_config_body("some_invalid_name", {})

    def test_user_off_boarded_only_once(self):
        deployment = Deployment(
            name="Test Deployment", duration="PT1M", features=Features(offBoarding=True)
        )
        authz_user = get_authz_user(onboarded=True, deployment=deployment)
        authz_user.user.boardingStatus = BoardingStatus(
            status=BoardingStatus.Status.OFF_BOARDED,
            reasonOffBoarded=BoardingStatus.ReasonOffBoarded.USER_NO_CONSENT,
            updateDateTime=datetime(year=2020, month=10, day=1),
        )

        manager = BoardingManager(authz_user, "/data", "")
        mock_module = MagicMock()
        mock_module.has_offboarding = True
        manager._enabled_boarding_modules = [mock_module]
        with self.assertRaises(OffBoardingRequiredError):
            manager.check_off_boarding_and_raise_error()
            mock_module.check_if_user_off_boarded_and_raise_error.assert_not_called()


if __name__ == "__main__":
    unittest.main()
