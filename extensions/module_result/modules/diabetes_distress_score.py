from pathlib import Path
from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Questionnaire,
    DiabetesDistressScore,
    Primitive,
    QuestionnaireAnswer,
)
from extensions.module_result.modules.module import Module
from extensions.module_result.questionnaires.diabetes_distress_score_calculator import (
    DiabetesDistressScoreCalculator,
)
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils.validators import read_json_file


class DiabetesDistressScoreModule(Module):
    moduleId = "DiabetesDistressScore"
    primitives = [Questionnaire, DiabetesDistressScore]
    calculator = DiabetesDistressScoreCalculator
    answers: list[QuestionnaireAnswer]
    ragEnabled = True

    def preprocess(self, primitives: list[Questionnaire], user: Optional[User]):
        if not primitives:
            return
        for primitive in list(primitives):
            if type(primitive) is not Questionnaire:
                raise InvalidRequestException("Only questionnaire can be submitted")

            self.answers = primitive.answers

            dds_dict = {
                **primitive.to_dict(include_none=False),
                **{DiabetesDistressScore.TOTAL_DDS: 0.0},
            }

            primitives.append(DiabetesDistressScore.from_dict(dds_dict))

    def calculate(self, primitive: Questionnaire):
        self.calculator().calculate(primitive, self.answers)

    def get_validation_schema(self):
        return read_json_file(
            "./schemas/questionnaire_schema.json", Path(__file__).parent
        )

    def get_threshold_data(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive] = None,
    ) -> dict:
        if isinstance(target_primitive, Questionnaire):
            return {}
        return super(DiabetesDistressScoreModule, self).get_threshold_data(
            target_primitive, module_config, primitives
        )
