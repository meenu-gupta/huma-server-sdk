import re
from collections import defaultdict
from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Questionnaire,
    QuestionnaireAnswer,
    Primitive,
    KCCQ,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionConfig,
)
from extensions.module_result.module_result_utils import config_body_to_question_map
from extensions.module_result.modules.questionnaire import QuestionnaireModule
from extensions.module_result.questionnaires.kccq_questionnaire_calculator import (
    KCCQQuestionnaireCalculator,
)
from sdk.common.exceptions.exceptions import (
    InvalidRequestException,
)


class KCCQQuestionnaireModule(QuestionnaireModule):
    moduleId = "KCCQ"
    primitives = [Questionnaire, KCCQ]
    calculator = KCCQQuestionnaireCalculator
    usesListStringTranslation: bool = False
    validation_schema_path = "./schemas/kccq_questionnaire_schema.json"
    partitioned_answers: dict
    ragEnabled = True

    def preprocess(self, primitives: list[Questionnaire], user: Optional[User]):
        primitive = primitives[0]
        if not isinstance(primitive, Questionnaire):
            raise InvalidRequestException("Only questionnaire can be submitted")

        self.partitioned_answers = defaultdict(list)
        self._partition_answers(primitive.answers)
        self._check_answered_required_questions()

        kccq_data = {
            **primitive.to_dict(include_none=False),
            **{key: 0.0 for key in KCCQ.__annotations__.keys()},
        }
        kccq = KCCQ.from_dict(kccq_data)
        kccq.partitioned_answers = self.partitioned_answers
        primitives.append(kccq)
        super().preprocess(primitives, user)

    @property
    def _min_answers_allowed(self):
        return {
            KCCQ.SUBSCALE_PHYSICAL_LIMITATION: 4,
            KCCQ.SUBSCALE_SYMPTOM_STABILITY: 1,
            KCCQ.SUBSCALE_SYMPTOM_FREQUENCY: 2,
            KCCQ.SUBSCALE_SYMPTOM_BURDEN: 2,
            KCCQ.SUBSCALE_SELF_EFFICACY: 1,
            KCCQ.SUBSCALE_QUALITY_OF_LIFE: 2,
            KCCQ.SUBSCALE_SOCIAL_LIMITATION: 3,
        }

    def _is_answer_to_be_included(
        self, question: dict, answer: QuestionnaireAnswer
    ) -> bool:
        skip_by_weight = question.get(QuestionConfig.SKIP_BY_WEIGHT)
        answer_weight = self._get_answer_weight(question, answer)
        return skip_by_weight is None or answer_weight != skip_by_weight

    def _partition_answers(self, answers: list[QuestionnaireAnswer]):
        question_id_expr = re.compile(
            r"kccq_(?P<subscale>.*?)_q(?P<questionNumber>\d+)(?P<questionSubNumber>[a-z])*$"
        )
        question_map = config_body_to_question_map(self.config.get_config_body())

        for answer in answers:
            question_id_match = question_id_expr.match(answer.questionId)
            if not question_id_match:
                raise InvalidRequestException(
                    "Wrong answer questionId it should be kccq_subscale_questionNumber[questionSubNumber]"
                )
            question_parts = question_id_match.groupdict()
            question = question_map.get(answer.questionId)
            if not question:
                continue

            if self._is_answer_to_be_included(question, answer):
                self.partitioned_answers[question_parts["subscale"]].append(
                    {
                        "questionNumber": int(question_parts["questionNumber"]),
                        "questionSubNumber": question_parts["questionSubNumber"],
                        "answer": answer,
                    }
                )

    def _check_answered_required_questions(self):
        for subscale, answers in self._min_answers_allowed.items():
            if len(self.partitioned_answers[subscale]) < answers:
                msg = f"Answered only {len(self.partitioned_answers[subscale])} for {subscale}. Min {answers} answers are required."
                raise NotAllRequiredQuestionsAnsweredException(msg)

    def get_threshold_data(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive] = None,
    ) -> dict:
        if not isinstance(target_primitive, KCCQ):
            return {}

        return super(KCCQQuestionnaireModule, self).get_threshold_data(
            target_primitive, module_config, primitives
        )
