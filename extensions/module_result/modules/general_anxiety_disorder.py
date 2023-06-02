from pathlib import Path
from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.models.primitives import Questionnaire, Primitive
from extensions.module_result.module_result_utils import (
    check_answered_required_questions,
)
from sdk.common.utils.validators import read_json_file
from .questionnaire import QuestionnaireModule


class GeneralAnxietyDisorderModule(QuestionnaireModule):
    moduleId = "GeneralAnxietyDisorder"
    primitives = [Questionnaire]
    ragEnabled = True

    def get_validation_schema(self):
        return read_json_file(
            "./schemas/questionnaire_schema.json", Path(__file__).parent
        )

    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        for primitive in primitives:
            if isinstance(primitive, Questionnaire):
                check_answered_required_questions(primitive, self.config.configBody)

        super(GeneralAnxietyDisorderModule, self).preprocess(primitives, user)
