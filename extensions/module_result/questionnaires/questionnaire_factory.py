from typing import Optional

from . import (
    DeprecatedEQ5DQuestionnaireCalculator,
    PAMQuestionnaireCalculator,
    QuestionnaireCalculator,
    SimpleScoreCalculator,
)
from ..models.module_config import ModuleConfig


class QuestionnaireCalculatorFactory:
    @staticmethod
    def retrieve_calculator(
        module_config: ModuleConfig,
    ) -> Optional[QuestionnaireCalculator]:
        config_body = module_config.configBody or {}
        if config_body.get("questionnaireType") == "EQ5D_5L":
            return DeprecatedEQ5DQuestionnaireCalculator()
        elif config_body.get("questionnaireType") == "PAM":
            return PAMQuestionnaireCalculator()
        elif config_body.get("isPAM", False):
            return PAMQuestionnaireCalculator()
        elif config_body.get("scoreAvailable", False):
            return SimpleScoreCalculator()
        else:
            return None
