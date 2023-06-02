import unittest
from unittest.mock import MagicMock

from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire, Lysholm
from extensions.module_result.modules import LysholmTegnerModule
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_lysholm_and_tegner,
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
    data = sample_lysholm_and_tegner()
    data.update({Questionnaire.USER_ID: TEST_USER_ID})
    return Questionnaire.from_dict(data)


sample_config_body = {
    "id": "lysholmtegner_configbody",
    "isForManager": False,
    "publisherName": "SK",
    "questionnaireName": "Lysholm Knee Scoring Scale & Tegner Activity Level Score",
    "name": "Lysholm Knee Scoring Scale & Tegner Activity Level Score",
    "maxScore": 100,
    "calculatedQuestionnaire": True,
    "questionnaireId": "koos_womac_module",
    "pages": [
        {
            "type": "INFO",
            "id": "lysholm_tegner_info",
            "order": 1,
            "displayInCP": False,
            "text": "Lysholm Knee Scoring Scale & Tegner Activity Level Score",
            "description": "Please answer every section and select which best applies to you at this moment. During the Tegner questionnaire, you will be asked your activity levels before your injury, current Activity level and activity level following surgery if applicable.",
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "id": "lysholm_limp",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Section 1 - LIMP",
                    "options": [
                        {
                            "label": "I have no limp when I walk",
                            "value": "0",
                            "weight": 5,
                        },
                        {
                            "label": "I have a slight or periodical limp when I walk",
                            "value": "1",
                            "weight": 3,
                        },
                        {
                            "label": "I have a severe and constant limp when I walk",
                            "value": "2",
                            "weight": 0,
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
                    "description": "",
                    "id": "lysholm_cane_or_crutches",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Section 2 - Using cane or crutches",
                    "options": [
                        {
                            "label": "I do not use a cane or crutches",
                            "value": "0",
                            "weight": 5,
                        },
                        {
                            "label": "I use a cane or crutches with some weight-bearing",
                            "value": "1",
                            "weight": 2,
                        },
                        {
                            "label": "Putting weight on my hurt leg is impossible",
                            "value": "2",
                            "weight": 0,
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
                    "id": "lysholm_locking_sensation",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Section 3 - Locking sensation in the knee",
                    "options": [
                        {
                            "label": "I have no locking and no catching sensation in my knee",
                            "value": "0",
                            "weight": 15,
                        },
                        {
                            "label": "I have catching sensation but no locking sensation in my knee",
                            "value": "1",
                            "weight": 10,
                        },
                        {
                            "label": "My knee locks occasionally",
                            "value": "2",
                            "weight": 6,
                        },
                        {
                            "label": "My knee locks frequently",
                            "value": "3",
                            "weight": 2,
                        },
                        {
                            "label": "My knee feels locked at this moment",
                            "value": "4",
                            "weight": 0,
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
                    "id": "lysholm_givingway_sensation",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Section 4 - Giving way sensation from the knee",
                    "options": [
                        {
                            "label": "My knee never gives way",
                            "value": "0",
                            "weight": 25,
                        },
                        {
                            "label": "My knee rarely gives way, only during athletics or vigorous activity",
                            "value": "1",
                            "weight": 20,
                        },
                        {
                            "label": "My knee frequently gives way during athletics or other vigorous activities. In turn I am unable to participate in these activities",
                            "value": "2",
                            "weight": 15,
                        },
                        {
                            "label": "My knee frequently gives way during daily activities",
                            "value": "3",
                            "weight": 10,
                        },
                        {
                            "label": "My knee often gives way during daily activities",
                            "value": "4",
                            "weight": 5,
                        },
                        {
                            "label": "My knee gives way every step I take",
                            "value": "5",
                            "weight": 0,
                        },
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
                    "id": "lysholm_pain",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Section 5 - Pain",
                    "options": [
                        {
                            "label": "I have no pain in my knee",
                            "value": "0",
                            "weight": 25,
                        },
                        {
                            "label": "I have intermittent or slight pain in my knee during vigorous activities",
                            "value": "1",
                            "weight": 20,
                        },
                        {
                            "label": "I have marked pain in my knee during vigorous activities",
                            "value": "2",
                            "weight": 15,
                        },
                        {
                            "label": "I have marked pain in my knee during or after walking more than 1 mile",
                            "value": "3",
                            "weight": 10,
                        },
                        {
                            "label": "I have marked pain in my knee during or after walking less than 1 mile",
                            "value": "4",
                            "weight": 5,
                        },
                        {
                            "label": "I have constant pain in my knee",
                            "value": "5",
                            "weight": 5,
                        },
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
                    "id": "lysholm_swelling",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Section 6 - Swelling",
                    "options": [
                        {
                            "label": "I have no swelling in my knee",
                            "value": "0",
                            "weight": 10,
                        },
                        {
                            "label": "I have swelling in my knee only after vigorous activities",
                            "value": "1",
                            "weight": 6,
                        },
                        {
                            "label": "I have swelling in my knee after ordinary activities",
                            "value": "2",
                            "weight": 2,
                        },
                        {
                            "label": "I have swelling constantly in my knee",
                            "value": "3",
                            "weight": 0,
                        },
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
                    "id": "lysholm_climbing_stairs",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Section 7 - Climbing stairs",
                    "options": [
                        {
                            "label": "I have no problems climbing stairs",
                            "value": "0",
                            "weight": 10,
                        },
                        {
                            "label": "I have slight problems climbing stairs",
                            "value": "1",
                            "weight": 6,
                        },
                        {
                            "label": "I can climb stairs only one at a time",
                            "value": "2",
                            "weight": 2,
                        },
                        {
                            "label": "Climbing stairs is impossible for me",
                            "value": "3",
                            "weight": 0,
                        },
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
                    "id": "lysholm_squatting",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Section 8 - Squatting",
                    "options": [
                        {
                            "label": "I have no problems squatting",
                            "value": "0",
                            "weight": 5,
                        },
                        {
                            "label": "I have slight problems squatting",
                            "value": "1",
                            "weight": 4,
                        },
                        {
                            "label": "I cannot squat beyond a 90° bend in my knee",
                            "value": "2",
                            "weight": 2,
                        },
                        {
                            "label": "Squatting is impossible because of my knee",
                            "value": "3",
                            "weight": 0,
                        },
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
                    "id": "tegner_activity_level_before",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Please select the highest level of activity that you participated in BEFORE YOUR INJURY",
                    "options": [
                        {
                            "label": "Level 10 <br> Competitive sports - soccer, football, rugby (national elite)",
                            "value": "0",
                            "weight": 10,
                        },
                        {
                            "label": "Level 9 Competitive sports - soccer, football, rugby (lower divisions), ice hockey, wrestling, gymnastics, basketball",
                            "value": "1",
                            "weight": 9,
                        },
                        {
                            "label": "Level 8 Competitive sports - racquetball or bandy, squash or badminton, track and field athletics (jumping, etc.), down-hill skiing",
                            "value": "2",
                            "weight": 8,
                        },
                        {
                            "label": "Level 7 Competitive sports - racquetball or bandy, squash or badminton, track and field athletics (jumping, etc.), down-hill skiing",
                            "value": "3",
                            "weight": 7,
                        },
                        {
                            "label": "Level 6 Recreational sports - tennis and badminton, handball, racquetball, down-hill skiing, jogging at least 5 times per week",
                            "value": "4",
                            "weight": 6,
                        },
                        {
                            "label": "Level 5 Work - heavy labor (construction, etc.) Competitive sports - cycling, cross-country skiing, Recreational sports - jogging on uneven ground at least twice weekly",
                            "value": "5",
                            "weight": 5,
                        },
                        {
                            "label": "Level 4 Work - moderately heavy labor (e.g. truck driving, etc.)",
                            "value": "6",
                            "weight": 4,
                        },
                        {
                            "label": "Level 3 Work - light labor (nursing, etc.)",
                            "value": "7",
                            "weight": 3,
                        },
                        {
                            "label": "Level 2 Work - light laborWalking on uneven ground possible, but impossible to back pack or hike",
                            "value": "8",
                            "weight": 2,
                        },
                        {
                            "label": "Level 1 Work - sedentary (secretarial, etc.)",
                            "value": "9",
                            "weight": 1,
                        },
                        {
                            "label": "Level 0 Sick leave or disability pension because of knee problems",
                            "value": "10",
                            "weight": 0,
                        },
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 12,
        },
        {
            "type": "INFO",
            "id": "koos_pain_info",
            "order": 13,
            "displayInCP": True,
            "text": " ",
            "description": "hu_koos_pain_extrainfo_text",
        },
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "id": "tegner_activity_level_current",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Please select the highest level of activity that you are CURRENTLY able to participate in",
                    "options": [
                        {
                            "label": "Level 10 <br> Competitive sports - soccer, football, rugby (national elite)",
                            "value": "0",
                            "weight": 10,
                        },
                        {
                            "label": "Level 9 Competitive sports - soccer, football, rugby (lower divisions), ice hockey, wrestling, gymnastics, basketball",
                            "value": "1",
                            "weight": 9,
                        },
                        {
                            "label": "Level 8 Competitive sports - racquetball or bandy, squash or badminton, track and field athletics (jumping, etc.), down-hill skiing",
                            "value": "2",
                            "weight": 8,
                        },
                        {
                            "label": "Level 7 Competitive sports - racquetball or bandy, squash or badminton, track and field athletics (jumping, etc.), down-hill skiing",
                            "value": "3",
                            "weight": 7,
                        },
                        {
                            "label": "Level 6 Recreational sports - tennis and badminton, handball, racquetball, down-hill skiing, jogging at least 5 times per week",
                            "value": "4",
                            "weight": 6,
                        },
                        {
                            "label": "Level 5 Work - heavy labor (construction, etc.) Competitive sports - cycling, cross-country skiing, Recreational sports - jogging on uneven ground at least twice weekly",
                            "value": "5",
                            "weight": 5,
                        },
                        {
                            "label": "Level 4 Work - moderately heavy labor (e.g. truck driving, etc.)",
                            "value": "6",
                            "weight": 4,
                        },
                        {
                            "label": "Level 3 Work - light labor (nursing, etc.)",
                            "value": "7",
                            "weight": 3,
                        },
                        {
                            "label": "Level 2 Work - light laborWalking on uneven ground possible, but impossible to back pack or hike",
                            "value": "8",
                            "weight": 2,
                        },
                        {
                            "label": "Level 1 Work - sedentary (secretarial, etc.)",
                            "value": "9",
                            "weight": 1,
                        },
                        {
                            "label": "Level 0 Sick leave or disability pension because of knee problems",
                            "value": "10",
                            "weight": 0,
                        },
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 14,
        },
    ],
    "submissionPage": {
        "type": "SUBMISSION",
        "id": "lysholm_tegner_submission",
        "order": 51,
        "text": "You’ve completed the questionnaire. Scroll up to change any of your answers. Changing answers may add new questions",
        "buttonText": "Submit",
        "description": "hu_koos_submission_description",
    },
}


class LysholmTegnerModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        server_config = MagicMock()
        server_config.server = Server(hostUrl="localhost")
        version = Version(server=VersionField("1.17.1"), api="api", build="build")
        self.module_config = ModuleConfig(
            moduleId=LysholmTegnerModule.__name__,
            configBody=sample_config_body,
        )

        def configure_with_binder(binder: Binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind(Version, version)
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(config=configure_with_binder)

    def test_questionnaire_preprocess_empty_answers(self):
        module = LysholmTegnerModule()
        module.config = self.module_config
        primitive = questionnaire_primitive()
        primitive.answers = []
        primitives = [primitive]

        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, user())

    def test_success_create_lysholm_and_tegner(self):
        module = LysholmTegnerModule()
        module.config = self.module_config
        primitives = [questionnaire_primitive()]
        module.preprocess(primitives, user())

        self.assertEqual(3, len(primitives))

    def test_success_calculate_lysholm_field(self):
        module = LysholmTegnerModule()
        module.config = self.module_config
        primitives = [questionnaire_primitive()]
        module.preprocess(primitives, user())

        lysholm_primitive = next(
            iter([p for p in primitives if isinstance(p, Lysholm)])
        )

        self.assertEqual(97, lysholm_primitive.lysholm)
