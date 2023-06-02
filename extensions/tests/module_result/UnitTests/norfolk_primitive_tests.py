import unittest
from unittest.mock import MagicMock

from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire, Primitive
from extensions.module_result.modules import NorfolkQuestionnaireModule
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_norfolk_questionnaire_module_data,
    sample_norfolk_questionnaire_missing_answers,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import PhoenixServerConfig, Server
from sdk.versioning.models.version import Version
from sdk.versioning.models.version_field import VersionField

CLIENT_ID = "c1"
PROJECT_ID = "p1"
USER_ID = "6131bdaaf9af87a4f08f4d02"


class NORFOLKModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        server_config = MagicMock()
        server_config.server = Server(hostUrl="localhost")
        version = Version(server=VersionField("1.17.1"), api="api", build="build")
        self.module_config = ModuleConfig(
            moduleId=NorfolkQuestionnaireModule.__name__, configBody={}
        )

        def configure_with_binder(binder: Binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind(Version, version)
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(config=configure_with_binder)

    def test_success_calculate_norfolk_score(self):
        module = NorfolkQuestionnaireModule()
        module.config = self.module_config
        module.calculator._get_answer_weight = MagicMock(return_value=2)
        primitives = [
            Questionnaire.from_dict(
                {
                    **sample_norfolk_questionnaire_module_data(),
                    Primitive.USER_ID: USER_ID,
                }
            )
        ]
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.config = self.module_config
        module.calculate(primitives[1])
        norfolk_primitive = primitives[1]
        self.assertEqual(norfolk_primitive.totalQolScore, 70.0)
        self.assertEqual(norfolk_primitive.physicalFunctionLargeFiber, 30.0)
        self.assertEqual(norfolk_primitive.activitiesOfDailyLiving, 10.0)
        self.assertEqual(norfolk_primitive.symptoms, 16.0)
        self.assertEqual(norfolk_primitive.smallFiber, 8.0)
        self.assertEqual(norfolk_primitive.automic, 6.0)

    def test_failure_not_enough_answers_norfolk_questionnaire(self):
        module = NorfolkQuestionnaireModule()
        primitives = [
            Questionnaire.from_dict(
                {
                    **sample_norfolk_questionnaire_missing_answers(),
                    Primitive.USER_ID: USER_ID,
                }
            )
        ]
        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, MagicMock())
