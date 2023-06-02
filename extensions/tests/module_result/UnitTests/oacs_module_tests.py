import unittest
from unittest.mock import MagicMock

from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire
from extensions.module_result.modules import OACSModule
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.module_result.IntegrationTests.test_samples import sample_oacs
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
    data = sample_oacs()
    data.update({Questionnaire.USER_ID: TEST_USER_ID})
    return Questionnaire.from_dict(data)


sample_config_body = {
    "id": "oacs_configbody",
    "isForManager": False,
    "publisherName": "SK",
    "questionnaireName": "OACS",
    "name": "OACS",
    "maxScore": 50,
    "calculatedQuestionnaire": True,
    "questionnaireId": "oacs_module",
    "pages": [
        {
            "type": "INFO",
            "id": "oacs_info1",
            "order": 1,
            "displayInCP": False,
            "name": "OACS",
            "text": "<b>Oxford Arthroplasty Early Change Score (OACS)</b>",
            "description": "Don't spend too long on any one question. Your first choice of response is typically the right one. Please answer <b>ALL</b> questions. This questionnaire asks about your health <u><b>today compared to before your operation.</b></u>",
        },
        {
            "type": "INFO",
            "id": "oacs_info2",
            "order": 2,
            "displayInCP": False,
            "name": "OACS",
            "text": "Thinking about the state of your health <u><b>before the operation</b></u>, how would you rate the following?",
            "description": "",
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_1",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your ability to stand compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 3,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_2",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your ability to walk compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 4,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_3",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your ability to walk up stairs compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 5,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_4",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your ability to walk down stairs compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 6,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_5",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your strength compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 7,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_6",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "How comfortable you feel when sitting compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 8,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_7",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your pain in the affected area compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 9,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_8",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your pain in the affected area when walking compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 10,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_9",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your appetite compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 11,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_10",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your mood compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 12,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_11",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your energy level compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 13,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_12",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your sleep compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 14,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_13",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "How you feel overall compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 15,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Change Score",
                    "id": "oacs_14",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your pain when trying to sleep compared to before the operation?",
                    "options": [
                        {"label": "Much worse", "value": "-2", "weight": -2},
                        {"label": "Worse", "value": "-1", "weight": -1},
                        {"label": "The same", "value": "0", "weight": 0},
                        {"label": "Better", "value": "1", "weight": 1},
                        {"label": "Much better", "value": "2", "weight": 2},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 16,
        },
    ],
    "submissionPage": {
        "type": "SUBMISSION",
        "name": "OACS",
        "id": "oacs_submission",
        "order": 51,
        "text": "You've completed the questionnaire.",
        "buttonText": "Submit",
        "description": "Scroll up to change any of your answers.",
    },
}


class OACSModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        server_config = MagicMock()
        server_config.server = Server(hostUrl="localhost")
        version = Version(server=VersionField("1.17.1"), api="api", build="build")
        self.module_config = ModuleConfig(
            moduleId=OACSModule.moduleId,
            configBody=sample_config_body,
        )

        def configure_with_binder(binder: Binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind(Version, version)
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(config=configure_with_binder)

    def test_failure_questionnaire_preprocess_empty_answers(self):
        module = OACSModule()
        module.config = self.module_config
        primitive = questionnaire_primitive()
        primitive.answers = []
        primitives = [primitive]

        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, user())

    def test_failure_questionnaire_preprocess_below_minimum_answers(self):
        module = OACSModule()
        module.config = self.module_config
        primitive = questionnaire_primitive()
        primitive.answers = primitive.answers[0:11]
        primitives = [primitive]

        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, user())

    def test_success_create_oacs(self):
        module = OACSModule()
        module.config = self.module_config
        primitives = [questionnaire_primitive()]
        module.preprocess(primitives, user())

        self.assertEqual(2, len(primitives))

    def test_success_calculate_oacs_score_field(self):
        module = OACSModule()
        primitives = [questionnaire_primitive()]
        module.config = self.module_config
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.calculate(primitives[1])
        oacs_primitive = primitives[1]

        self.assertIsNotNone(oacs_primitive.oacsScore)
        self.assertEqual(oacs_primitive.oacsScore, -1.9)

    def test_success_calculate_oacs_score_field_with_a_skipped_question(self):
        module = OACSModule()
        primitive = questionnaire_primitive()
        primitive.answers = primitive.answers[0:13]
        primitive.answers[:-1]
        module.config = self.module_config
        primitives = [primitive]
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.calculate(primitives[1])
        oacs_primitive = primitives[1]

        self.assertIsNotNone(oacs_primitive.oacsScore)
        self.assertEqual(oacs_primitive.oacsScore, -1.9)
