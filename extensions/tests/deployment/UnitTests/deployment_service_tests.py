import unittest
from unittest.mock import patch, MagicMock

from extensions.authorization.exceptions import WrongActivationOrMasterKeyException
from extensions.authorization.models.role.default_permissions import PermissionType
from extensions.authorization.models.role.role import Role
from extensions.deployment.exceptions import ModuleWithPrimitiveDoesNotExistException
from extensions.deployment.models.activation_code import ActivationCode
from extensions.deployment.models.care_plan_group import CarePlanGroup
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.deployment import (
    Deployment,
    ChangeType,
    OnboardingModuleConfig,
)
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import LearnSection, LearnArticle
from extensions.deployment.models.status import EnableStatus
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.exceptions import EncryptionSecretNotAvailable
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.modules import default_modules
from sdk.common.exceptions.exceptions import InvalidRequestException

SAMPLE_ID = "620cfed9367840eabbaf8ccb"
SERVICE_PATH = "extensions.deployment.service.deployment_service"


class MockRepo(MagicMock):
    create_deployment = MagicMock(return_value=SAMPLE_ID)
    create_deployment_revision = MagicMock()
    retrieve_deployments = MagicMock()
    retrieve_deployments_by_ids = MagicMock()
    retrieve_deployment = MagicMock()
    retrieve_deployment_by_activation_code = MagicMock()
    update_key_action = MagicMock(return_value=("", False))


class MockConsentRepo(MagicMock):
    create_consent = MagicMock()
    retrieve_signed_econsent_logs = MagicMock()
    retrieve_econsent_pdfs = MagicMock()


class MockConfig(MagicMock):
    class MockServer:
        class MockDep:
            encryptionSecret = ""

        deployment = MockDep()

    server = MockServer()


class DeploymentServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.service = DeploymentService(
            MockRepo(),
            MockConsentRepo(),
            MockConfig(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            None,
        )

    def tearDown(self) -> None:
        MockRepo.create_deployment.reset_mock()
        MockRepo.create_deployment_revision.reset_mock()
        MockRepo.retrieve_deployments.reset_mock()
        MockRepo.retrieve_deployments_by_ids.reset_mock()
        MockRepo.retrieve_deployment.reset_mock()
        MockRepo.retrieve_deployment_by_activation_code.reset_mock()

        MockConsentRepo.create_consent.reset_mock()
        MockConsentRepo.retrieve_econsent_pdfs.reset_mock()
        MockConsentRepo.retrieve_signed_econsent_logs.reset_mock()

    @patch(f"{SERVICE_PATH}.inject", MagicMock())
    def test_create_deployment(self):
        deployment = Deployment(id=SAMPLE_ID)
        self.service.create_deployment(deployment)

    def test_create_deployment_revision(self):
        deployment = Deployment(id=SAMPLE_ID)
        self.service.create_deployment_revision(
            deployment, ChangeType.DEPLOYMENT, SAMPLE_ID, SAMPLE_ID
        )
        MockRepo.create_deployment_revision.assert_called_once()

    def test_create_consent(self):
        consent = Consent()
        self.service.create_consent(SAMPLE_ID, consent)
        MockConsentRepo.create_consent.assert_called_once()

    @patch(f"{SERVICE_PATH}.remove_none_values", MagicMock(return_value={}))
    def test_create_or_update_module_config(self):
        module_config = ModuleConfig(id="module_test3")
        self.service.create_or_update_module_config(SAMPLE_ID, module_config)

    @patch(f"{SERVICE_PATH}.remove_none_values", MagicMock(return_value={}))
    def test_update_module_config(self):
        module_config = ModuleConfig(id="module_test3")
        self.service.update_module_config(SAMPLE_ID, module_config)

    def test__are_deployments_dicts_equal(self):
        self.service._are_deployments_dicts_equal({}, {})

    def test_create_learn_section(self):
        learn_section = LearnSection(id=SAMPLE_ID)
        self.service.create_learn_section(SAMPLE_ID, learn_section)

    @patch(f"{SERVICE_PATH}.remove_none_values", MagicMock(return_value={}))
    def test_create_or_update_onboarding_module_config(self):
        onboarding_module_config = OnboardingModuleConfig(
            onboardingId="Consent", status=EnableStatus.DISABLED
        )
        self.service.create_or_update_onboarding_module_config(
            SAMPLE_ID, onboarding_module_config
        )

    @patch(f"{SERVICE_PATH}.remove_none_values", MagicMock(return_value={}))
    def test_update_onboarding_module_config(self):
        onboarding_module_config = OnboardingModuleConfig(
            onboardingId="Consent", status=EnableStatus.DISABLED
        )
        self.service.update_onboarding_module_config(
            SAMPLE_ID, onboarding_module_config
        )

    def test_create_article(self):
        learn_article = LearnArticle(id=SAMPLE_ID)
        self.service.create_article(SAMPLE_ID, SAMPLE_ID, learn_article)

    @patch(f"{SERVICE_PATH}.inject", MagicMock())
    def test_create_key_action(self):
        key_action_config = KeyActionConfig(id=SAMPLE_ID)
        self.service.create_key_action(SAMPLE_ID, key_action_config)

    def test_retrieve_deployments(self):
        self.service.retrieve_deployments()

    def test_retrieve_deployments_by_ids(self):
        self.service.retrieve_deployments_by_ids([SAMPLE_ID])

    def test_retrieve_deployment(self):
        self.service.retrieve_deployment(SAMPLE_ID)

    def test_retrieve_deployment_by_version_number(self):
        self.service.retrieve_deployment_by_version_number(SAMPLE_ID, 1)

    def test_retrieve_deployment_config(self):
        class MockAuthUser:
            class MockDeployment:
                apply_care_plan_by_id = MagicMock()

            deployment = MockDeployment()
            deployment_id = MagicMock()
            get_role = MagicMock()
            id = MagicMock()
            user = MagicMock()

        mock_auth_user = MockAuthUser()
        self.service.retrieve_deployment_config(mock_auth_user)

    def test_retrieve_deployment_with_code(self):
        with self.assertRaises(WrongActivationOrMasterKeyException):
            self.service.retrieve_deployment_with_code("code")

    def test__retrieve_deployment_with_code(self):
        activation_code = ActivationCode("17024567")
        with self.assertRaises(InvalidRequestException):
            self.service._retrieve_deployment_with_code(activation_code)

    @patch(f"{SERVICE_PATH}.inject", MagicMock())
    def test_retrieve_modules(self):
        self.service.retrieve_modules()

    @patch(f"{SERVICE_PATH}.inject")
    def test_retrieve_module(self, mock_inject):
        class MockInstance(MagicMock):
            modules = default_modules

        mock_inject.instance = MockInstance()
        self.service.retrieve_module("AZGroupKeyActionTrigger")
        with self.assertRaises(ModuleWithPrimitiveDoesNotExistException):
            self.service.retrieve_module("AZGroupKeyActionTrigger1")

    def test_retrieve_module_configs(self):
        self.service.retrieve_module_configs(SAMPLE_ID)

    def test_check_field_value_exists_in_module_config(self):
        self.service.check_field_value_exists_in_module_config("", "")

    def test_retrieve_onboarding_module_configs(self):
        self.service.retrieve_onboarding_module_configs(SAMPLE_ID)

    def test_retrieve_module_config(self):
        self.service.retrieve_module_config(SAMPLE_ID)

    def test_retrieve_key_actions(self):
        self.service.retrieve_key_actions(SAMPLE_ID, KeyActionConfig.Trigger.SURGERY)

    @patch(f"{SERVICE_PATH}.remove_none_values", MagicMock(return_value={}))
    def test_update_deployment(self):
        deployment = Deployment(id=SAMPLE_ID)
        self.service.update_deployment(deployment)

    def test_update_enrollment_counter(self):
        self.service.update_enrollment_counter(SAMPLE_ID)

    def test_update_learn_section(self):
        self.service.update_learn_section(SAMPLE_ID, LearnSection(id=SAMPLE_ID))

    def test_update_article(self):
        self.service.update_article(SAMPLE_ID, SAMPLE_ID, LearnArticle(id=SAMPLE_ID))

    def test_update_key_action(self):
        self.service.update_key_action(SAMPLE_ID, KeyActionConfig(id=SAMPLE_ID))

    @patch(f"{SERVICE_PATH}.inject", MagicMock())
    def test_delete_deployment(self):
        self.service.delete_deployment(SAMPLE_ID)

    @patch(f"{SERVICE_PATH}.remove_none_values", MagicMock(return_value={}))
    def test_delete_module_config(self):
        self.service.delete_module_config(SAMPLE_ID, SAMPLE_ID)

    @patch(f"{SERVICE_PATH}.remove_none_values", MagicMock(return_value={}))
    def test_delete_onboarding_module_config(self):
        self.service.delete_onboarding_module_config(SAMPLE_ID, SAMPLE_ID)

    @patch(f"{SERVICE_PATH}.inject", MagicMock())
    def test_delete_key_action(self):
        self.service.delete_key_action(SAMPLE_ID, SAMPLE_ID)

    def test_is_consent_signed(self):
        self.service.is_consent_signed(SAMPLE_ID, Deployment(id=SAMPLE_ID))

    def test_encrypt_value(self):
        with self.assertRaises(EncryptionSecretNotAvailable):
            self.service.encrypt_value(SAMPLE_ID, "")

    def test_create_care_plan_group(self):
        group_mock = MagicMock()
        careplan_group = CarePlanGroup(groups=[group_mock])
        self.service.create_care_plan_group(SAMPLE_ID, careplan_group)

    def test_create_or_update_roles(self):
        roles = [Role(permissions=[PermissionType.EDIT_ROLE_PERMISSIONS])]
        self.service.create_or_update_roles(SAMPLE_ID, roles)

    def test_retrieve_user_care_plan_group_log(self):
        self.service.retrieve_user_care_plan_group_log(SAMPLE_ID, SAMPLE_ID)

    def test_retrieve_user_notes(self):
        self.service.retrieve_user_notes(SAMPLE_ID, SAMPLE_ID)

    def test_create_econsent(self):
        self.service.create_econsent(SAMPLE_ID, EConsent(id=SAMPLE_ID))

    def test_is_econsent_signed(self):
        self.service.is_econsent_signed(SAMPLE_ID, Deployment(id=SAMPLE_ID))

    @patch(f"{SERVICE_PATH}.AuthorizedUser")
    def test_retrieve_econsent_logs(self, mock_auth_user):
        mock_auth_user.id = SAMPLE_ID
        mock_auth_user.is_user = MagicMock(return_value=True)
        self.service.retrieve_econsent_logs(SAMPLE_ID, mock_auth_user(), False)
