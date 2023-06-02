import unittest
from unittest.mock import MagicMock

from extensions.module_result.modules import QuestionnaireModule
from extensions.module_result.questionnaires import (
    DeprecatedEQ5DQuestionnaireCalculator,
    PAMQuestionnaireCalculator,
    SimpleScoreCalculator,
)
from extensions.module_result.questionnaires.questionnaire_factory import (
    QuestionnaireCalculatorFactory,
)


class QuestionnaireCalculatorFactoryTestCase(unittest.TestCase):
    @staticmethod
    def get_module_config(config_body: dict) -> MagicMock:
        module_config = MagicMock()
        module_config.configBody = config_body
        return module_config

    def test_deprecated_EQ5D_5L_calculator(self):
        module_config = self.get_module_config(
            {QuestionnaireModule.QUESTIONNAIRE_TYPE: "EQ5D_5L"}
        )
        calculator = QuestionnaireCalculatorFactory
        res = calculator.retrieve_calculator(module_config)
        self.assertTrue(isinstance(res, DeprecatedEQ5DQuestionnaireCalculator))

    def test_PAM_calculator(self):
        pam_configs = [{QuestionnaireModule.QUESTIONNAIRE_TYPE: "PAM"}, {"isPAM": True}]
        for config in pam_configs:
            module_config = self.get_module_config(config)
            calculator = QuestionnaireCalculatorFactory
            res = calculator.retrieve_calculator(module_config)
            self.assertTrue(isinstance(res, PAMQuestionnaireCalculator))

    def test_simple_score_calculator(self):
        module_config = self.get_module_config({"scoreAvailable": True})
        calculator = QuestionnaireCalculatorFactory
        res = calculator.retrieve_calculator(module_config)
        self.assertTrue(isinstance(res, SimpleScoreCalculator))

    def test_no_available_calculator(self):
        module_config = self.get_module_config({})
        calculator = QuestionnaireCalculatorFactory
        res = calculator.retrieve_calculator(module_config)
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
