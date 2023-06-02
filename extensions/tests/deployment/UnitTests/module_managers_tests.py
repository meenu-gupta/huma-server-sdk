import copy
import unittest
from unittest.mock import PropertyMock, patch, MagicMock

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.deployment.models.deployment import OnboardingModuleConfig, Deployment
from extensions.authorization.boarding.manager import BoardingManager
from extensions.authorization.boarding.module import BoardingModule
from extensions.deployment.models.status import EnableStatus

MODULE_CONFIG_ID = "604773187773c9a6ab284fc7"
USER_ID = "60477662de201b24e1225e3a"
DEPLOYMENT_ID = "604776819a60ee5c4f8d43ae"
TEST_CLASS_NAME = "BoardingTestClass"

DEFAULT_MODULES_PATH = (
    "extensions.authorization.boarding.manager.BoardingManager.default_modules"
)

ONBOARDING_CONFIG_DICT = {
    OnboardingModuleConfig.ID: MODULE_CONFIG_ID,
    OnboardingModuleConfig.ONBOARDING_ID: TEST_CLASS_NAME,
    OnboardingModuleConfig.STATUS: EnableStatus.ENABLED.name,
    OnboardingModuleConfig.ORDER: 1,
    OnboardingModuleConfig.CONFIG_BODY: {
        "enabled": "ENABLED",
        "instituteFullName": "string",
        "instituteName": "string",
        "instituteTextDetails": "string",
        "sections": [
            {
                "type": "DATA_GATHERING",
                "title": "Your data",
                "details": "some details",
            },
            {
                "type": "AGREEMENT",
                "title": "Agreement",
                "options": [
                    {
                        "type": 0,
                        "order": 0,
                        "text": "some text",
                    },
                    {
                        "type": 1,
                        "order": 1,
                        "text": "some text",
                    },
                ],
            },
            {
                "type": "FEEDBACK",
                "title": "Feedback",
                "details": "some details",
            },
        ],
    },
}

ONBOARDING_MODULE_CONFIG = OnboardingModuleConfig.from_dict(ONBOARDING_CONFIG_DICT)

MODULE_CONFIGS = [ONBOARDING_MODULE_CONFIG]


class MockG:
    authz_user = MagicMock()
    authz_user.deployment_id.return_value = "some_deployment_id"


class MockDeploymentService:
    retrieve_deployment = MagicMock(
        return_value=Deployment(onboardingConfigs=MODULE_CONFIGS)
    )


class MockDeploymentWithDisabledModule:
    configs = copy.deepcopy(ONBOARDING_CONFIG_DICT)
    configs[OnboardingModuleConfig.STATUS] = EnableStatus.DISABLED.name
    disabled_module_config = OnboardingModuleConfig.from_dict(configs)
    onboardingConfigs = [disabled_module_config]


class MockDeployment:
    onboardingConfigs = [OnboardingModuleConfig.from_dict(ONBOARDING_CONFIG_DICT)]


class BoardingTestClass(BoardingModule):
    name = "BoardingTestClass"
    onboardingConfig = None

    def order(self):
        return 1

    def preprocess(self):
        pass

    def validate_config_body(self, config_body):
        pass

    def process(self):
        pass

    def is_module_completed(self, authz_user: AuthorizedUser) -> bool:
        pass

    def validate_if_allowed_to_reach_route(self, authz_user: AuthorizedUser, path: str):
        pass

    def check_if_user_off_boarded_and_raise_error(self, authz_user: AuthorizedUser):
        pass


class MockAuthzUser:
    @property
    def deployment(self):
        return MockDeployment()


class MockAuthzUserWithDisabledModule:
    @property
    def deployment(self):
        return MockDeploymentWithDisabledModule()


class OnboardingModuleManagerTestCase(unittest.TestCase):
    @patch(DEFAULT_MODULES_PATH, new_callable=PropertyMock)
    def test_success_load_configs(self, default_modules):
        default_modules.return_value = [BoardingTestClass]
        manager = BoardingManager(MockAuthzUser(), "", "")
        self.assertEqual(len(manager._enabled_boarding_modules), 1)

    @patch(DEFAULT_MODULES_PATH, new_callable=PropertyMock)
    def test_disabled_onboarding_module(self, default_modules):
        default_modules.return_value = [BoardingTestClass]
        manager = BoardingManager(MockAuthzUserWithDisabledModule(), "", "")
        self.assertEqual(len(manager._enabled_boarding_modules), 0)


if __name__ == "__main__":
    unittest.main()
