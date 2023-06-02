from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.models.primitives import (
    Questionnaire,
    Lysholm,
    Tegner,
    Primitive,
    QuestionnaireAnswer,
)
from extensions.module_result.module_result_utils import (
    check_answered_required_questions,
    config_body_to_question_map,
)
from extensions.module_result.modules.questionnaire import QuestionnaireModule
from sdk.common.exceptions.exceptions import InvalidRequestException


class LysholmTegnerModule(QuestionnaireModule):
    moduleId = "LysholmTegner"
    primitives = [Questionnaire, Lysholm, Tegner]
    ragEnabled = True

    def _create_tegner_primitive(
        self,
        questionnaire: Questionnaire,
        question_map: dict,
        answer_map: dict[str, QuestionnaireAnswer],
    ) -> Tegner:

        tegner_question_ids = {
            Tegner.ACTIVITY_LEVEL_BEFORE: "tegner_activity_level_before",
            Tegner.ACTIVITY_LEVEL_CURRENT: "tegner_activity_level_current",
        }
        answer_weights = {}
        for field, question_id in tegner_question_ids.items():
            question = question_map.get(question_id)
            answer = answer_map.get(question_id)
            answer_weights[field] = self._get_answer_weight(question, answer)

        primitive_dict = {**questionnaire.to_dict(include_none=False), **answer_weights}

        return Tegner.from_dict(primitive_dict)

    def _create_lysholm_primitive(
        self,
        questionnaire: Questionnaire,
        question_map: dict,
        answer_map: dict[str, QuestionnaireAnswer],
    ) -> Lysholm:
        lysholm_question_ids = {
            Lysholm.LIMP: "lysholm_limp",
            Lysholm.CANE_OR_CRUTCHES: "lysholm_cane_or_crutches",
            Lysholm.LOCKING_SENSATION: "lysholm_locking_sensation",
            Lysholm.GIVING_WAY_SENSATION: "lysholm_givingway_sensation",
            Lysholm.PAIN: "lysholm_pain",
            Lysholm.SWELLING: "lysholm_swelling",
            Lysholm.CLIMBING_STAIRS: "lysholm_climbing_stairs",
            Lysholm.SQUATTING: "lysholm_squatting",
        }
        answer_weights = {}
        for field, question_id in lysholm_question_ids.items():
            question = question_map.get(question_id)
            answer = answer_map.get(question_id)
            answer_weights[field] = self._get_answer_weight(question, answer)

        primitive_dict = {
            **questionnaire.to_dict(include_none=False),
            **answer_weights,
            Lysholm.LYSHOLM: sum(answer_weights.values()),
        }

        return Lysholm.from_dict(primitive_dict)

    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        primitive = primitives[0]
        if not isinstance(primitive, Questionnaire):
            raise InvalidRequestException("Only questionnaire can be submitted")

        check_answered_required_questions(primitive, self.config.configBody)

        question_map = config_body_to_question_map(self.config.configBody)
        answer_map = {answer.questionId: answer for answer in primitive.answers}

        primitives.append(
            self._create_tegner_primitive(primitive, question_map, answer_map)
        )
        primitives.append(
            self._create_lysholm_primitive(primitive, question_map, answer_map)
        )

        return super(LysholmTegnerModule, self).preprocess(primitives, user)
