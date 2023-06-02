from pathlib import Path
from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire, Primitive
from extensions.module_result.models.primitives.primitive_koos_womac_questionnaire import (
    KOOS,
    WOMAC,
)
from extensions.module_result.modules.questionnaire import QuestionnaireModule
from extensions.module_result.questionnaires.koos_score_calculator import (
    KOOSQuestionnaireCalculator,
    ADL,
    PAIN,
    SYMPTOMS,
    SPORT_RECREATION,
    QUALITY_OF_LIFE,
)
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils.validators import read_json_file


class KOOSQuestionnaireModule(QuestionnaireModule):
    moduleId = "KOOS"
    primitives = [Questionnaire, KOOS, WOMAC]
    usesListStringTranslation: bool = False
    calculator = KOOSQuestionnaireCalculator
    validation_schema_path = "./schemas/koos_questionnaire_schema.json"
    ragEnabled = True

    @property
    def _min_answers_allowed(self):
        return {
            ADL: 9,
            PAIN: 5,
            SYMPTOMS: 4,
            SPORT_RECREATION: 3,
            QUALITY_OF_LIFE: 2,
        }

    def get_validation_schema(self):
        return read_json_file(
            "./schemas/koos_questionnaire_schema.json", Path(__file__).parent
        )

    def preprocess(self, primitives: list[Questionnaire], user: Optional[User]):
        primitive = primitives[0]
        if not isinstance(primitive, Questionnaire):
            raise InvalidRequestException("Only questionnaire can be submitted")

        self._check_answered_required_questions(
            [q.questionId for q in primitive.answers]
        )

        koos_primitive = KOOS.from_dict(
            {
                **primitive.to_dict(include_none=False),
                **{key: 0.0 for key in KOOS.__annotations__.keys()},
            }
        )
        primitives.append(koos_primitive)

        womac_primitive = WOMAC.from_dict(
            {
                **primitive.to_dict(include_none=False),
                **{key: 0.0 for key in WOMAC.__annotations__.keys()},
            }
        )
        primitives.append(womac_primitive)

        super().preprocess(primitives, user)

    def _check_answered_required_questions(self, question_ids: list[str]):
        occurrences = {
            ADL: 0,
            PAIN: 0,
            SYMPTOMS: 0,
            SPORT_RECREATION: 0,
            QUALITY_OF_LIFE: 0,
        }
        for question in question_ids:
            for key in occurrences:
                if question.startswith(key):
                    occurrences[key] += 1

        for key, value in self._min_answers_allowed.items():
            if value > occurrences[key]:
                msg = f"Answered only {occurrences[key]} for {key}. Min {value} answers are required."
                raise NotAllRequiredQuestionsAnsweredException(msg)

    def filter_results(
        self,
        primitives: list[Primitive],
        module_configs: list[ModuleConfig],
        is_for_user=False,
    ) -> list[Primitive]:
        return primitives

    def get_threshold_data(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive] = None,
    ) -> dict:
        if not isinstance(target_primitive, (KOOS, WOMAC)):
            return {}

        return super(KOOSQuestionnaireModule, self).get_threshold_data(
            target_primitive, module_config, primitives
        )
