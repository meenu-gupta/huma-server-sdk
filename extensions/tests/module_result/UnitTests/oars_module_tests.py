import unittest
from unittest.mock import MagicMock

from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire, OARS
from extensions.module_result.modules import OARSModule
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.module_result.IntegrationTests.test_samples import sample_oars
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
    data = sample_oars()
    data.update({Questionnaire.USER_ID: TEST_USER_ID})
    return Questionnaire.from_dict(data)


sample_config_body = {
    "id": "oars_configbody",
    "isForManager": False,
    "publisherName": "SK",
    "questionnaireName": "OARS",
    "name": "OARS",
    "maxScore": 50,
    "calculatedQuestionnaire": True,
    "questionnaireId": "oars_module",
    "localizationPrefix": "hu_oars",
    "pages": [
        {
            "type": "INFO",
            "id": "oars_info1",
            "order": 1,
            "displayInCP": False,
            "name": "OARS",
            "text": "<b>Oxford Arthroplasty Early Recovery Score (OARS)</b>",
            "description": "Don’t spend too long on any one question. Your first choice of response is typically the right one. Please answer <b>ALL</b> questions. This questionnaire asks about your health <u><b>today.</b></u>",
        },
        {
            "type": "INFO",
            "id": "oars_info2",
            "order": 2,
            "displayInCP": False,
            "name": "OARS",
            "text": "How much do you agree with these statements?",
            "description": "",
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_1",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "I've felt unwell",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_2",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "I've felt tired",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_3",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "I've felt faint",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_4",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "It's been painful in the affected area",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_5",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "I've had pain at night in the affected area",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_6",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "The affected area has felt swollen",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_7",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "I've had difficulty getting into bed",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_8",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "I've not been able to stand",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_9",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "I've not been able to walk",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_10",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "I've not slept well",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_11",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "I've found it difficult to sleep",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "I've not been able to sleep due to the pain in the affected area",
                    "id": "oars_12",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Your sleep compared to before the operation?",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_13",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "I've felt sick",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
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
                    "name": "The Oxford Arthroplasty Early Recovery Score",
                    "id": "oars_14",
                    "required": False,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "I've lost my appetite",
                    "options": [
                        {"label": "Strongly disagree", "value": "4", "weight": 4},
                        {"label": "Disagree", "value": "3", "weight": 3},
                        {
                            "label": "Neither agree nor disagree",
                            "value": "2",
                            "weight": 2,
                        },
                        {"label": "Agree", "value": "1", "weight": 1},
                        {"label": "Strongly agree", "value": "0", "weight": 0},
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 16,
        },
    ],
    "submissionPage": {
        "type": "SUBMISSION",
        "name": "OARS",
        "id": "oars_submission",
        "order": 51,
        "text": "You've completed the questionnaire.",
        "buttonText": "Submit",
        "description": "Scroll up to change any of your answers.",
    },
}


class OARSModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        server_config = MagicMock()
        server_config.server = Server(hostUrl="localhost")
        version = Version(server=VersionField("1.17.1"), api="api", build="build")
        self.module_config = ModuleConfig(
            moduleId=OARSModule.moduleId,
            configBody=sample_config_body,
        )

        def configure_with_binder(binder: Binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind(Version, version)
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(config=configure_with_binder)

    def test_failure_questionnaire_preprocess_empty_answers(self):
        module = OARSModule()
        module.config = self.module_config
        primitive = questionnaire_primitive()
        primitive.answers = []
        primitives = [primitive]

        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, user())

    def test_failure_questionnaire_preprocess_below_minimum_answers(self):
        module = OARSModule()
        module.config = self.module_config
        primitive = questionnaire_primitive()
        primitive.answers = primitive.answers[0:11]
        primitives = [primitive]

        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, user())

    def test_success_create_oars(self):
        module = OARSModule()
        module.config = self.module_config
        primitives = [questionnaire_primitive()]
        module.preprocess(primitives, user())

        self.assertEqual(2, len(primitives))

    def test_success_calculate_oars_score_field(self):
        module = OARSModule()
        primitives = [questionnaire_primitive()]
        module.config = self.module_config
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.calculate(primitives[1])
        oars_primitive = primitives[1]

        self._assert_scores_values(primitive=oars_primitive, expected_oars_score=66.1)

    def test_success_calculate_oars_score_field_with_a_skipped_question(self):
        module = OARSModule()
        primitive = questionnaire_primitive()
        primitive.answers = primitive.answers[0:12]
        primitive.answers[:-1]
        module.config = self.module_config
        primitives = [primitive]
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.calculate(primitives[1])
        oars_primitive = primitives[1]

        self._assert_scores_values(primitive=oars_primitive, expected_oars_score=72.9)

    def _assert_scores_values(self, primitive: OARS, expected_oars_score: float):
        self.assertIsNotNone(primitive.oarsScore)
        self.assertIsNotNone(primitive.painScore)
        self.assertIsNotNone(primitive.mobilityScore)
        self.assertIsNotNone(primitive.nauseaScore)
        self.assertIsNotNone(primitive.sleepScore)
        self.assertEqual(primitive.oarsScore, expected_oars_score)
