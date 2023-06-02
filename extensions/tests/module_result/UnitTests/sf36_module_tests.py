import unittest
from unittest.mock import MagicMock

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Questionnaire,
    Primitive,
    QuestionnaireAnswer,
)
from extensions.module_result.modules import SF36QuestionnaireModule
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_sf36_data,
    sample_sf36_question_map,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import PhoenixServerConfig, Server
from sdk.versioning.models.version import Version
from sdk.versioning.models.version_field import VersionField

CLIENT_ID = "c1"
PROJECT_ID = "p1"


class SF36QuestionnaireModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        server_config = MagicMock()
        server_config.server = Server(hostUrl="localhost")
        version = Version(server=VersionField("1.17.1"), api="api", build="build")
        self.module_config = ModuleConfig(
            moduleId=SF36QuestionnaireModule.__name__, configBody={}
        )

        def configure_with_binder(binder: Binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind(Version, version)
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(config=configure_with_binder)

    def test_success_calculate_sf36_score(self):
        module = SF36QuestionnaireModule()
        module.config = self.module_config
        implementation = module.calculator._get_answer_weight
        module.calculator._get_answer_weight = MagicMock(return_value=3)
        primitives = [
            Questionnaire.from_dict(
                {**sample_sf36_data(), Primitive.USER_ID: "6131bdaaf9af87a4f08f4d02"}
            )
        ]
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.config = self.module_config
        module.calculate(primitives[1])
        sf36_primitive = primitives[1]
        self.assertEqual(sf36_primitive.physicalFunctioningScore, 3.0)
        self.assertEqual(sf36_primitive.limitationsPhysicalHealthScore, 3.0)
        self.assertEqual(sf36_primitive.limitationsEmotionalProblemsScore, 3.0)
        self.assertEqual(sf36_primitive.energyFatigueScore, 3.0)
        self.assertEqual(sf36_primitive.emotionalWellBeingScore, 3.0)
        self.assertEqual(sf36_primitive.socialFunctioningScore, 3.0)
        self.assertEqual(sf36_primitive.painScore, 3.0)
        self.assertEqual(sf36_primitive.generalHealthScore, 3.0)
        module.calculator._get_answer_weight = implementation

    def test_success_weight_calculation(self):
        module = SF36QuestionnaireModule()
        module.config = self.module_config
        question_map = sample_sf36_question_map()
        all_answers = sample_sf36_data()[Questionnaire.ANSWERS]
        answers = []
        for question in question_map:
            answer = next(filter(lambda x: x["questionId"] == question, all_answers))
            answers.append(QuestionnaireAnswer.from_dict(answer))

        calculator = module.calculator()
        self.assertEqual(calculator._get_answer_weight(question_map, answers[0]), 100)
        self.assertEqual(calculator._get_answer_weight(question_map, answers[1]), 100)
        self.assertEqual(calculator._get_answer_weight(question_map, answers[2]), 0)
