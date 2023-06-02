from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.primitives import Questionnaire
from extensions.module_result.questionnaires.fjs_calculator import FJSScoreCalculator
from .questionnaire import QuestionnaireModule


class FJSBaseModule(QuestionnaireModule):
    moduleId = "Unknown"
    primitives = [Questionnaire]
    calculator = FJSScoreCalculator
    validation_schema_path = "./schemas/fjs_questionnaire_schema.json"
    min_answers = 8

    def preprocess(self, primitives: list[Questionnaire], user: Optional[User]):
        answers = primitives[0].answers
        if len(answers) < self.min_answers:
            msg = f"Answered only {len(answers)} questions. {self.min_answers} answers are required."
            raise NotAllRequiredQuestionsAnsweredException(msg)

        super().preprocess(primitives, user)
