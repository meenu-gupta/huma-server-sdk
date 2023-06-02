import unittest
from datetime import datetime
from unittest.mock import MagicMock

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Questionnaire,
    DiabetesDistressScore,
)
from extensions.module_result.models.primitives import QuestionnaireAnswer
from extensions.module_result.modules.diabetes_distress_score import (
    DiabetesDistressScoreModule,
)
from extensions.module_result.modules.modules_manager import ModulesManager
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import Server, PhoenixServerConfig
from sdk.versioning.models.version import Version
from sdk.versioning.models.version_field import VersionField

DDS_PATH = "extensions.module_result.modules.diabetes_distress_score"


def _questionnaire_sample(answers_amount=None):
    answers = [
        {
            QuestionnaireAnswer.QUESTION: "Test1",
            QuestionnaireAnswer.ANSWER_TEXT: "A serious problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test2",
            QuestionnaireAnswer.ANSWER_TEXT: "A slight problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test3",
            QuestionnaireAnswer.ANSWER_TEXT: "Not a problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test4",
            QuestionnaireAnswer.ANSWER_TEXT: "A slight problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test5",
            QuestionnaireAnswer.ANSWER_TEXT: "Not a problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test6",
            QuestionnaireAnswer.ANSWER_TEXT: "A slight problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test7",
            QuestionnaireAnswer.ANSWER_TEXT: "Not a problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test8",
            QuestionnaireAnswer.ANSWER_TEXT: "A slight problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test9",
            QuestionnaireAnswer.ANSWER_TEXT: "Not a problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test10",
            QuestionnaireAnswer.ANSWER_TEXT: "A slight problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test11",
            QuestionnaireAnswer.ANSWER_TEXT: "Not a problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test12",
            QuestionnaireAnswer.ANSWER_TEXT: "A slight problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test13",
            QuestionnaireAnswer.ANSWER_TEXT: "Not a problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test14",
            QuestionnaireAnswer.ANSWER_TEXT: "A slight problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test15",
            QuestionnaireAnswer.ANSWER_TEXT: "A serious problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test16",
            QuestionnaireAnswer.ANSWER_TEXT: "A slight problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test17",
            QuestionnaireAnswer.ANSWER_TEXT: "A very serious problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test18",
            QuestionnaireAnswer.ANSWER_TEXT: "A slight problem",
        },
        {
            QuestionnaireAnswer.QUESTION: "Test19",
            QuestionnaireAnswer.ANSWER_TEXT: "Not a problem",
        },
    ]
    if answers_amount:
        answers = answers[:answers_amount]

    return Questionnaire.from_dict(
        {
            Questionnaire.USER_ID: "5e8f0c74b50aa9656c34789a",
            Questionnaire.MODULE_ID: "DiabetesDistressScore",
            Questionnaire.DEVICE_NAME: "iOS",
            Questionnaire.DEPLOYMENT_ID: "5e8f0c74b50aa9656c34789c",
            Questionnaire.START_DATE_TIME: datetime.utcnow(),
            Questionnaire.ANSWERS: answers,
            Questionnaire.QUESTIONNAIRE_ID: "test_id",
            Questionnaire.QUESTIONNAIRE_NAME: "test_name",
        }
    )


class DiabetesDistressScoreUnitTest(unittest.TestCase):
    def setUp(self) -> None:
        server_config = MagicMock()
        server_config.server = Server(hostUrl="localhost")
        version = Version(server=VersionField("1.17.1"), api="api", build="build")
        self.module_config = ModuleConfig(
            moduleId=DiabetesDistressScoreModule.__name__, configBody={}
        )

        def configure_with_binder(binder: Binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind(Version, version)
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(config=configure_with_binder)

    def test_dds_2_calculations_logic(self):
        module = DiabetesDistressScoreModule()
        module.config = self.module_config
        primitives = [_questionnaire_sample(answers_amount=2)]
        module.preprocess(primitives, None)

        # testing that DDS primitive was appended to initial primitives list
        self.assertEqual(len(primitives), 2)

        module.calculate(primitives[-1])
        dds: DiabetesDistressScore = primitives[-1]
        self.assertTrue(isinstance(dds, DiabetesDistressScore))
        self.assertEqual(3.5, dds.totalDDS)
        self.assertIsNone(dds.emotionalBurden)
        self.assertIsNone(dds.physicianDistress)
        self.assertIsNone(dds.regimenDistress)
        self.assertIsNone(dds.interpersonalDistress)

    def test_dds_17_calculations_logic(self):
        module = DiabetesDistressScoreModule()
        module.config = self.module_config
        primitives = [_questionnaire_sample()]
        module.preprocess(primitives, None)

        # testing that DDS primitive was appended to initial primitives list
        self.assertEqual(len(primitives), 2)

        module.calculate(primitives[-1])
        dds: DiabetesDistressScore = primitives[-1]
        self.assertTrue(isinstance(dds, DiabetesDistressScore))
        self.assertEqual(2.0, dds.totalDDS)
        self.assertEqual(1.4, dds.emotionalBurden)
        self.assertEqual(2.75, dds.physicianDistress)
        self.assertEqual(1.8, dds.regimenDistress)
        self.assertEqual(2.33, dds.interpersonalDistress)
