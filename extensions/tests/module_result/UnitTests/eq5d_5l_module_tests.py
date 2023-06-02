import unittest
from unittest.mock import MagicMock

from extensions.authorization.models.user import User
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Questionnaire,
    QuestionnaireAnswer,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionAnswerFormat,
)
from extensions.module_result.modules import EQ5D5LModule
from extensions.module_result.modules.eq5d_5l import TOGGLE_INDEX_VALUE
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_eq5d_questionnaire_result,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import Server, PhoenixServerConfig
from sdk.versioning.models.version import Version
from sdk.versioning.models.version_field import VersionField

TEST_DEPLOYMENT_ID = "5e8f0c74b50aa9656c34789c"
TEST_USER_ID = "5e8f0c74b50aa9656c34789a"
TEST_CONFIG_ID = "5d386cc6ff885918d96edb4a"


def user():
    return User(id=TEST_USER_ID)


def questionnaire_primitive():
    data = sample_eq5d_questionnaire_result()
    data.update({Questionnaire.USER_ID: TEST_USER_ID})
    return Questionnaire.from_dict(data)


sample_config_body = {
    "isForManager": False,
    "name": "EQ5D5L",
    "publisherName": "RT",
    "id": "582e7145-3767-4c43-a783-0617437919e6",
    "region": "UK",
    "scoreAvailable": True,
    "trademarkText": "©EuroQol Research Foundation.EQ–5D™ is a trade mark of the EuroQol Research foundation",
    "isHorizontalFlow": True,
    "questionnaireType": "EQ5D_5L",
    "pages": [
        {
            "type": "INFO",
            "id": "eb58b951-cf4d-49c3-bc08-8a852e6ee240",
            "order": 1,
            "text": "<b>EQ-5D-5L</b>",
            "description": "On the following screens, please tap the statement that best describes your health today.",
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "id": "hu_eq5d5l_mobility",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "<b>Your mobility TODAY</b>",
                    "shortText": "Mobility",
                    "options": [
                        {
                            "label": "I have no problems in walking about",
                            "value": "1",
                            "weight": 1,
                        },
                        {
                            "label": "I have slight problems in walking about",
                            "value": "2",
                            "weight": 2,
                        },
                        {
                            "label": "hu_eq5d5l_mob_label1",
                            "value": "3",
                            "weight": 3,
                        },
                        {
                            "label": "I have severe problems in walking about",
                            "value": "4",
                            "weight": 4,
                        },
                        {
                            "label": "I am unable to walk about",
                            "value": "5",
                            "weight": 5,
                        },
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 2,
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "id": "hu_eq5d5l_selfcare",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "<b>Your self-care TODAY</b>",
                    "shortText": "Self-care",
                    "options": [
                        {
                            "label": "I have no problems washing or dressing myself",
                            "value": "1",
                            "weight": 1,
                        },
                        {
                            "label": "I have slight problems washing or dressing myself",
                            "value": "2",
                            "weight": 2,
                        },
                        {
                            "label": "hu_eq5d5l_selfcare_label3",
                            "value": "3",
                            "weight": 3,
                        },
                        {
                            "label": "I have severe problems washing or dressing myself",
                            "value": "4",
                            "weight": 4,
                        },
                        {
                            "label": "I am unable to wash or dress myself",
                            "value": "5",
                            "weight": 5,
                        },
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
                    "description": "(e.g. work, study, housework, family or leisure activities)",
                    "id": "hu_eq5d5l_usualactivity",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "<b>Your usual activities TODAY</b>",
                    "shortText": "Usual activities",
                    "options": [
                        {
                            "label": "I have no problems doing my usual activities",
                            "value": "1",
                            "weight": 1,
                        },
                        {
                            "label": "I have slight problems doing my usual activities",
                            "value": "2",
                            "weight": 2,
                        },
                        {
                            "label": "I have moderate problems doing my usual activities",
                            "value": "3",
                            "weight": 3,
                        },
                        {
                            "label": "hu_eq5d5l_usualactivity_label4",
                            "value": "4",
                            "weight": 4,
                        },
                        {
                            "label": "I am unable to do my usual activities",
                            "value": "5",
                            "weight": 5,
                        },
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
                    "id": "hu_eq5d5l_paindiscomfort",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "<b>Your pain / discomfort TODAY</b>",
                    "shortText": "Pain / discomfort",
                    "options": [
                        {
                            "label": "I have no pain or discomfort",
                            "value": "1",
                            "weight": 1,
                        },
                        {
                            "label": "I have slight pain or discomfort",
                            "value": "2",
                            "weight": 2,
                        },
                        {
                            "label": "I have moderate pain or discomfort",
                            "value": "3",
                            "weight": 3,
                        },
                        {
                            "label": "I have severe pain or discomfort",
                            "value": "4",
                            "weight": 4,
                        },
                        {
                            "label": "hu_eq5d5l_paindis_label5",
                            "value": "5",
                            "weight": 5,
                        },
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
                    "id": "hu_eq5d5l_anxiety",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "<b>Your anxiety / depression TODAY</b>",
                    "shortText": "Anxiety / depression",
                    "options": [
                        {
                            "label": "hu_eq5d5l_anxiety_label1",
                            "value": "1",
                            "weight": 1,
                        },
                        {
                            "label": "I am slightly anxious or depressed",
                            "value": "2",
                            "weight": 2,
                        },
                        {
                            "label": "I am moderately anxious or depressed",
                            "value": "3",
                            "weight": 3,
                        },
                        {
                            "label": "I am severely anxious or depressed",
                            "value": "4",
                            "weight": 4,
                        },
                        {
                            "label": "I am extremely anxious or depressed",
                            "value": "5",
                            "weight": 5,
                        },
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 6,
        },
        {
            "type": "INFO",
            "id": "0256ee11-9e6c-4589-9717-5ba7e7b2a0a6",
            "order": 7,
            "text": "We would like to know how good or bad your health is TODAY.",
            "description": "On the next screen you will see a scale number 0 to 100.<br><br>100 means the <u>best</u> health you can imagine.<br><br>0 means the <u>worst</u> health you can imagine.",
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "id": "hu_eq5d5l_scale",
                    "required": True,
                    "format": "SCALE",
                    "order": 1,
                    "text": "Please tap or drag the scale to indicate how your health is TODAY",
                    "shortText": "Self-rated health",
                    "lowerBound": "0",
                    "upperBound": "100",
                    "lowerBoundLabel": "The <u>worst</u> health you can imagine",
                    "upperBoundLabel": "The <u>best</u> health you can imagine",
                    "isVisualAnalogueScale": True,
                    "vasLabel": "YOUR HEALTH TODAY",
                    "stepLength": "1",
                }
            ],
            "order": 8,
        },
    ],
    "submissionPage": {
        "description": "If you would like to change any of your answers, you may do so pressing the “Back” button prior to finalizing the questionnaire.<br><br>Please finalize the questionnaire by pressing the “Finalize” button. Once you press “Finalize”, you will not be able to go back to review or change your answers.",
        "id": "c7c2ebc4-75b1-4872-8acd-1fd66f279a0e",
        "text": "You’ve completed the questionnaire",
        "buttonText": "Finalize",
        "order": 9,
        "type": "SUBMISSION",
    },
}


class EQ5D5LModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        server_config = MagicMock()
        server_config.server = Server(hostUrl="localhost")
        version = Version(server=VersionField("1.17.1"), api="api", build="build")
        self.module_config = ModuleConfig(
            moduleId=EQ5D5LModule.__name__,
            configBody=sample_config_body,
            id=TEST_CONFIG_ID,
        )

        def configure_with_binder(binder: Binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind(Version, version)
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(config=configure_with_binder)

    def test_success_calculate_eq5d_5l_score_field(self):
        module = EQ5D5LModule()
        primitives = [questionnaire_primitive()]
        module.config = self.module_config
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.calculate(primitives[1])
        self._verify_eq5_primitive(primitives[1])

    def test_calculate_eq5_no_answers(self):
        data = questionnaire_primitive()
        data.answers = []

        module = EQ5D5LModule()
        primitives = [data]
        module.config = self.module_config
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.calculate(primitives[1])
        eq5d_5l_primitive = primitives[1]

        items_to_check = [
            eq5d_5l_primitive.indexValue,
            eq5d_5l_primitive.healthState,
            eq5d_5l_primitive.mobility,
            eq5d_5l_primitive.selfCare,
            eq5d_5l_primitive.usualActivities,
            eq5d_5l_primitive.pain,
            eq5d_5l_primitive.anxiety,
            eq5d_5l_primitive.eqVas,
        ]
        for item in items_to_check:
            self.assertEqual(None, item)

    def test_calculate_eq5_more_then_required_answers(self):
        data = sample_eq5d_questionnaire_result()
        data.update({Questionnaire.USER_ID: TEST_USER_ID})
        data[Questionnaire.ANSWERS].append(
            {
                QuestionnaireAnswer.QUESTION_ID: "some new id",
                QuestionnaireAnswer.QUESTION: "Your usual activities TODAY",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.ANSWER_TEXT: "answer text",
            }
        )
        data = Questionnaire.from_dict(data)

        module = EQ5D5LModule()
        primitives = [data]
        module.config = self.module_config
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.calculate(primitives[1])
        self._verify_eq5_primitive(primitives[1])

    def _verify_eq5_primitive(self, eq5d_5l_primitive):
        self.assertEqual(0.036, eq5d_5l_primitive.indexValue)
        self.assertEqual(33451, eq5d_5l_primitive.healthState)
        self.assertEqual(3, eq5d_5l_primitive.mobility)
        self.assertEqual(3, eq5d_5l_primitive.selfCare)
        self.assertEqual(4, eq5d_5l_primitive.usualActivities)
        self.assertEqual(5, eq5d_5l_primitive.pain)
        self.assertEqual(1, eq5d_5l_primitive.anxiety)
        self.assertEqual(50, eq5d_5l_primitive.eqVas)

    def test_index_value_removed(self):
        module = EQ5D5LModule()
        primitives = [questionnaire_primitive()]
        module.config = self.module_config
        module.preprocess(primitives, user())
        module.calculate(primitives[1])
        module.change_primitives_based_on_config(primitives, [self.module_config])
        eq5_primitive = primitives[1]
        self.assertIsNone(eq5_primitive.indexValue)

    def test_index_value_present(self):
        module = EQ5D5LModule()
        primitives = [questionnaire_primitive()]
        config_body = sample_config_body.copy()
        config_body[TOGGLE_INDEX_VALUE] = True
        module_config = ModuleConfig(
            moduleId=EQ5D5LModule.__name__,
            configBody=config_body,
            id=TEST_CONFIG_ID,
        )
        module.config = module_config
        module.preprocess(primitives, user())
        module.calculate(primitives[1])
        module.change_primitives_based_on_config(primitives, [module_config])
        eq5_primitive = primitives[1]
        self.assertEqual(0.036, eq5_primitive.indexValue)
