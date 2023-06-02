import unittest
from unittest.mock import MagicMock

from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire
from extensions.module_result.modules import GeneralAnxietyDisorderModule
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_gad_7,
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


def gad_primitive():
    data = sample_gad_7()
    data.update({Questionnaire.USER_ID: TEST_USER_ID})
    return Questionnaire.from_dict(data)


sample_config_body = {
    "name": "Mental health: GAD-7",
    "id": "eeb23d05-d23f-4eb7-ad57-52d70a8edd29",
    "isForManager": False,
    "scoreAvailable": True,
    "publisherName": "AB",
    "trademarkText": "Developed by Drs. Robert L. Spitzer, Janet B.W. Williams, Kurt Kroenke and colleagues, with an educational grant from Pfizer Inc. No permission required to reproduce, translate, display or distribute.",
    "pages": [
        {
            "type": "QUESTION",
            "items": [
                {
                    "logic": {"isEnabled": False},
                    "description": "",
                    "id": "d571d295-9da6-4583-98dc-db92126a4f34",
                    "required": True,
                    "format": "TEXTCHOICE",
                    "order": 1,
                    "text": "Feeling nervous, anxious or on edge?",
                    "options": [
                        {
                            "label": "hu_norfolk_commonOp_notatall",
                            "value": "0",
                            "weight": 0,
                        },
                    ],
                    "selectionCriteria": "SINGLE",
                }
            ],
            "order": 2,
        },
    ],
}


class GAD7ModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        server_config = MagicMock()
        server_config.server = Server(hostUrl="localhost")
        version = Version(server=VersionField("1.17.1"), api="api", build="build")
        self.module_config = ModuleConfig(
            moduleId=GeneralAnxietyDisorderModule.__name__,
            configBody=sample_config_body,
        )

        def configure_with_binder(binder: Binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind(Version, version)
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(config=configure_with_binder)

    def test_questionnaire_preprocess_empty_answers(self):
        module = GeneralAnxietyDisorderModule()
        module.config = self.module_config
        primitive = gad_primitive()
        primitive.answers = []
        primitives = [primitive]

        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, user())
