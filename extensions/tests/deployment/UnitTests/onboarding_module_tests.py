import unittest

from extensions.authorization.models.role.role import Role
from extensions.deployment.models.deployment import OnboardingModuleConfig
from extensions.deployment.models.status import EnableStatus
from sdk.common.utils.convertible import ConvertibleClassValidationError

MODULE_CONFIG_ID = "604773187773c9a6ab284fc7"

ONBOARDING_CONFIG_DICT = {
    OnboardingModuleConfig.ID: MODULE_CONFIG_ID,
    OnboardingModuleConfig.ONBOARDING_ID: "EConsent",
    OnboardingModuleConfig.STATUS: EnableStatus.ENABLED.name,
    OnboardingModuleConfig.ORDER: 1,
    OnboardingModuleConfig.USER_TYPES: [Role.UserType.USER],
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


class OnboardingModuleConfigTestCase(unittest.TestCase):
    def test_success_creation_onboarding_config(self):
        ONBOARDING_CONFIG_DICT[OnboardingModuleConfig.ONBOARDING_ID] = "EConsent"
        try:
            OnboardingModuleConfig.from_dict(ONBOARDING_CONFIG_DICT)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_creation_onboarding_config_no_onboarding_id(self):
        ONBOARDING_CONFIG_DICT[OnboardingModuleConfig.ONBOARDING_ID] = None
        with self.assertRaises(ConvertibleClassValidationError):
            OnboardingModuleConfig.from_dict(ONBOARDING_CONFIG_DICT)

    def test_failure_no_order(self):
        ONBOARDING_CONFIG_DICT.pop(OnboardingModuleConfig.ONBOARDING_ID)
        with self.assertRaises(ConvertibleClassValidationError):
            OnboardingModuleConfig.from_dict(ONBOARDING_CONFIG_DICT)


if __name__ == "__main__":
    unittest.main()
