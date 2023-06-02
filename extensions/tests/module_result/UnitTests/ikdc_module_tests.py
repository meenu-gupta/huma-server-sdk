import unittest
from unittest.mock import MagicMock

from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire
from extensions.module_result.modules import IKDCModule
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_ikdc,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import Server, PhoenixServerConfig
from sdk.versioning.models.version import Version
from sdk.versioning.models.version_field import VersionField

TEST_DEPLOYMENT_ID = "5e8f0c74b50aa9656c34789c"
TEST_USER_ID = "5e8f0c74b50aa9656c34789a"


def user():
    return User(id=TEST_USER_ID)


def questionnaire_primitive():
    data = sample_ikdc()
    data.update({Questionnaire.USER_ID: TEST_USER_ID})
    return Questionnaire.from_dict(data)


sample_module_config = {
    "moduleId": "KneeHealthIKDC",
    "moduleName": "hu_ikdc_moduleName",
    "shortModuleName": "IKDC",
    "ragThresholds": [
        {
            "color": "#FBCCD7",
            "enabled": True,
            "fieldName": "value",
            "severity": 3,
            "thresholdRange": [{"minValue": 81, "maxValue": 100}],
            "type": "VALUE",
        },
        {
            "color": "#FFDA9F",
            "enabled": True,
            "fieldName": "value",
            "severity": 2,
            "thresholdRange": [{"minValue": 51, "maxValue": 80}],
            "type": "VALUE",
        },
        {
            "color": "#CBEBF0",
            "enabled": True,
            "fieldName": "value",
            "severity": 1,
            "thresholdRange": [{"minValue": 0, "maxValue": 50}],
            "type": "VALUE",
        },
    ],
    "schedule": {"friendlyText": "AS NEEDED", "timesOfDay": [], "timesPerDuration": 0},
    "notificationData": {
        "title": "hu_ikdc_notification_title",
        "body": "hu_ikdc_notification_body",
    },
    "status": "ENABLED",
    "about": "hu_ikdc_body",
    "order": 4,
    "configBody": {},
}


class IKDCModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        server_config = MagicMock()
        server_config.server = Server(hostUrl="localhost")
        version = Version(server=VersionField("1.17.1"), api="api", build="build")

        def configure_with_binder(binder: Binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind(Version, version)
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(config=configure_with_binder)
        self.module_config = ModuleConfig.from_dict(
            sample_module_config, use_validator_field=False
        )

    def test_failure_questionnaire_preprocess_empty_answers(self):
        module = IKDCModule()
        primitive = questionnaire_primitive()
        primitive.answers = []
        primitives = [primitive]
        module.config = module.extract_module_config(
            module_configs=[self.module_config], primitive=None
        )

        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, user())

    def test_failure_questionnaire_preprocess_below_minimum_answers(self):
        module = IKDCModule()
        module.config = module.extract_module_config(
            module_configs=[self.module_config], primitive=None
        )
        primitive = questionnaire_primitive()
        primitive.answers = primitive.answers[0:8]
        primitives = [primitive]

        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, user())

    def test_success_create_ikdc(self):
        module = IKDCModule()
        module.config = module.extract_module_config(
            module_configs=[self.module_config], primitive=None
        )
        primitives = [questionnaire_primitive()]
        module.preprocess(primitives, user())

        self.assertEqual(2, len(primitives))

    def test_success_calculate_ikdc_score_field(self):
        module = IKDCModule()
        primitives = [questionnaire_primitive()]
        module.config = module.extract_module_config(
            module_configs=[self.module_config], primitive=None
        )
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.calculate(primitives[1])
        ikdc_primitive = primitives[1]

        self.assertIsNotNone(ikdc_primitive.value)
        self.assertEqual(ikdc_primitive.value, 66.66666666666666)
