from abc import ABC

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire


class QuestionnaireCalculator(ABC):
    def calculate(self, primitive: Questionnaire, module_config: ModuleConfig):
        pass
