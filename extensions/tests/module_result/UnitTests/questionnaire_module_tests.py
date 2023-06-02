from typing import Any
import unittest

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.modules import QuestionnaireModule
from sdk.common.utils.convertible import ConvertibleClassValidationError

TEST_DEPLOYMENT_ID = "5e8f0c74b50aa9656c34789c"
TEST_USER_ID = "5e8f0c74b50aa9656c34789a"


def module_config_with_config_body(option: dict = None) -> dict:
    return {
        "calculatedQuestionnaire": False,
        "horizontalFlow": True,
        "isForManager": True,
        "isOnboarding": False,
        "name": "string",
        "pages": [
            {
                "items": [
                    {
                        "description": "",
                        "format": "TEXTCHOICE",
                        "id": "89b31c9b-211b-4adb-9122-d73edbb7331a",
                        "options": [
                            option or {"label": "None", "value": "1", "weight": 1},
                            {"label": "Mild", "value": "2", "weight": 2},
                        ],
                        "order": 1,
                        "required": True,
                        "selectionCriteria": "SINGLE",
                        "text": "How breathless are you when you are walking around or walking up stairs?",
                    }
                ],
                "order": 1,
                "type": "QUESTION",
            }
        ],
        "publisherName": "string",
        "region": "UK",
    }


class QuestionnaireModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.module_config_body = module_config_with_config_body()
        self.module_config = ModuleConfig(
            moduleId=QuestionnaireModule.__name__, configBody=self.module_config_body
        )

    def test_failure_questionnaire_validate_config_body_with_invalid_options(self):
        module = QuestionnaireModule()
        self._assert_module_config_body_validation_failed(options=None, module=module)
        self._assert_module_config_body_validation_failed(options=[], module=module)

    def test_success_questionnaire_validate_config_body_with_options(self):
        module = QuestionnaireModule()
        result = module.validate_config_body(module_config=self.module_config)
        self.assertIsNone(result)

    def _assert_module_config_body_validation_failed(
        self, options: Any, module: QuestionnaireModule
    ):
        module_config_body = self.module_config_body
        module_config_body["pages"][0]["items"][0]["options"] = options
        module_config = self.module_config
        module_config.configBody = module_config_body

        with self.assertRaises(ConvertibleClassValidationError):
            module.validate_config_body(module_config=module_config)
