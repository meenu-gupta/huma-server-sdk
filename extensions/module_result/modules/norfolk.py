from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Questionnaire,
    NORFOLK,
    QuestionnaireAnswer,
    Primitive,
)
from extensions.module_result.modules.licensed_questionnaire_module import (
    LicensedQuestionnaireModule,
)
from extensions.module_result.questionnaires.norfolk_questionnaire_calculator import (
    NorfolkQuestionnaireCalculator,
)
from sdk.common.exceptions.exceptions import InvalidRequestException


class NorfolkQuestionnaireModule(LicensedQuestionnaireModule):
    moduleId = "NORFOLK"
    primitives = [Questionnaire, NORFOLK]
    calculator = NorfolkQuestionnaireCalculator
    validation_schema_path = "./schemas/norfolk_questionnaire_schema.json"

    def preprocess(self, primitives: list[Questionnaire], user: Optional[User]):
        if len(primitives) != 1:
            raise InvalidRequestException("Only one primitive can be submitted")

        primitive = primitives[0]
        if not isinstance(primitive, Questionnaire):
            raise InvalidRequestException("Only questionnaire can be submitted")

        NORFOLK._answers = primitive.answers
        self._check_answered_required_questions(primitive.answers)

        norfolk_data = {
            **primitive.to_dict(include_none=False),
            **{key: 0.0 for key in NORFOLK.__annotations__.keys()},
        }

        # We should filter result if we have "None" selected in a few questions.
        # We should leave there only None and discard all other answers
        question_ids_we_should_discard_if_none_weight_found = {
            "hu_norfolk_symptom_q18",
            "hu_norfolk_symptom_q19",
            "hu_norfolk_symptom_q20",
            "hu_norfolk_symptom_q21",
            "hu_norfolk_symptom_q22",
            "hu_norfolk_symptom_q23",
            "hu_norfolk_symptom_q24",
        }
        none_answer_id = "hu_norfolk_commonOp_none"
        for answer in primitive.answers:
            if (
                answer.questionId in question_ids_we_should_discard_if_none_weight_found
                and none_answer_id in answer.answerText
            ):
                answer.answerText = none_answer_id

        norfolk = NORFOLK.from_dict(norfolk_data)
        norfolk._answers = primitive.answers
        primitives.append(norfolk)
        super().preprocess(primitives, user)

    @staticmethod
    def _check_answered_required_questions(answers: list[QuestionnaireAnswer]):
        required_answers = 47
        if len(answers) < required_answers:
            msg = f"Answered only {len(answers)} questions. {required_answers} answers are required."
            raise NotAllRequiredQuestionsAnsweredException(msg)

    def filter_results(
        self,
        primitives: list[Primitive],
        module_configs: list[ModuleConfig],
        is_for_user=False,
    ) -> list[Primitive]:
        if primitives and isinstance(primitives[0], NORFOLK):
            return primitives

        return super(NorfolkQuestionnaireModule, self).filter_results(
            primitives, module_configs, is_for_user
        )

    def get_threshold_data(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive] = None,
    ) -> dict:
        if not isinstance(target_primitive, NORFOLK):
            return {}

        return super(NorfolkQuestionnaireModule, self).get_threshold_data(
            target_primitive, module_config, primitives
        )
