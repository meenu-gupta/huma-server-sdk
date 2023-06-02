import unittest
from unittest.mock import MagicMock, patch

from extensions.module_result.modules.licensed_questionnaire_module import (
    LicensedQuestionnaireModule,
)
from extensions.tests.deployment.UnitTests.test_helpers import LICENSED_SAMPLE_KEY
from sdk.common.localization.utils import Language

LICENSED_QUESTIONNAIRE_PATH = (
    "extensions.module_result.modules.licensed_questionnaire_module"
)


class SampleModule(LicensedQuestionnaireModule):
    moduleId = "sample"


class LicencedQuestionnaireModuleTestCase(unittest.TestCase):
    @patch(f"{LICENSED_QUESTIONNAIRE_PATH}.super")
    @patch(f"{LICENSED_QUESTIONNAIRE_PATH}.ModuleConfig")
    def test_extract_module_config(self, module_config, mock_super):
        mock_super.return_value = MagicMock()
        result_config = SampleModule().extract_module_config(
            module_configs=[], primitive=None
        )
        self.assertEqual(module_config.from_dict(), result_config)

    def test_get_module_localization__en(self):
        expected_translation = {
            LICENSED_SAMPLE_KEY: "translation text for LicenseModule on en from file"
        }
        self._verify_translation_from_file(Language.EN, expected_translation)

    def test_get_module_localization__fr(self):
        expected_translation = {
            LICENSED_SAMPLE_KEY: "translation text for LicenseModule on fr from file"
        }
        self._verify_translation_from_file(Language.FR, expected_translation)

    def test_get_module_localization__file_not_exist_fallback_to_eng(self):
        expected_translation = {
            LICENSED_SAMPLE_KEY: "translation text for LicenseModule on en from file"
        }
        self._verify_translation_from_file("RU", expected_translation)

    def _verify_translation_from_file(self, language: str, expected_res: dict):
        result_translation = SampleModule().get_localization(language)
        self.assertEqual(expected_res, result_translation)


if __name__ == "__main__":
    unittest.main()
