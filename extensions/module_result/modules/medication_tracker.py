from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire, Primitives
from extensions.module_result.modules.questionnaire import QuestionnaireModule
from sdk.common.exceptions.exceptions import InvalidRequestException
from .visualizer import MedicationTrackerVisualizer


class MedicationTrackerModule(QuestionnaireModule):
    moduleId = "MedicationTracker"
    primitives = [Questionnaire]
    visualizer = MedicationTrackerVisualizer

    def preprocess(self, primitives: Primitives, user: Optional[User]):
        super().preprocess(primitives, user)
        for primitive in primitives:
            if primitive.answers:
                total_score = None
                try:
                    answer = primitive.answers[0].answerText
                    if answer is not None:
                        total_score = int(answer)
                except ValueError:
                    continue
                if total_score is not None and not (0 <= total_score <= 100):
                    raise InvalidRequestException(
                        "First answer should be int between 0 and 100"
                    )

    def calculate(self, primitive: Questionnaire):
        total_score = 0
        if primitive.answers:
            try:
                total_score = int(primitive.answers[0].answerText)
            except Exception:
                pass
        primitive.value = total_score

    def validate_config_body(self, module_config: ModuleConfig):
        pass
