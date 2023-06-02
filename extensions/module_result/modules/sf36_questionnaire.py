import re
from collections import defaultdict
from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Questionnaire,
    SF36,
    QuestionnaireAnswer,
    Primitive,
)
from extensions.module_result.modules.questionnaire import QuestionnaireModule
from extensions.module_result.questionnaires.sf36_questionnaire_calculator import (
    SF36QuestionnaireCalculator,
)
from sdk.common.exceptions.exceptions import InvalidRequestException


class SF36QuestionnaireModule(QuestionnaireModule):
    moduleId = "SF36"
    primitives = [Questionnaire, SF36]
    usesListStringTranslation: bool = False
    calculator = SF36QuestionnaireCalculator
    validation_schema_path = "./schemas/sf36_questionnaire_schema.json"

    def preprocess(self, primitives: list[Questionnaire], user: Optional[User]):
        if len(primitives) != 1:
            raise InvalidRequestException("Only one primitive can be submitted")
        primitive = primitives[0]
        if not isinstance(primitive, Questionnaire):
            raise InvalidRequestException(
                "Only questionnaire primitives can be submitted"
            )

        partitioned_answers = self._partition_answers(primitive.answers)
        sf36 = SF36.from_dict(primitive.to_dict(include_none=False))
        sf36._partitioned_answers = partitioned_answers
        primitives.append(sf36)
        super().preprocess(primitives, user)

    @staticmethod
    def _is_question_scored(question_number: str):
        return question_number != "2"

    def _partition_answers(self, answers: list[QuestionnaireAnswer]):
        partitioned_answers = defaultdict(list)
        question_id_expr = re.compile(
            r"sf36_(?P<subscale>.*?)_q(?P<questionNumber>\d+)(?P<questionSubNumber>[a-z])*$"
        )

        for answer in answers:
            question_id_match = question_id_expr.match(answer.questionId)
            if not question_id_match:
                raise InvalidRequestException(
                    "Wrong answer questionId it should be sf36_subscale_questionNumber[questionSubNumber]"
                )
            question_parts = question_id_match.groupdict()
            if self._is_question_scored(question_parts["questionNumber"]):
                partitioned_answers[question_parts["subscale"]].append(
                    {
                        "questionNumber": int(question_parts["questionNumber"]),
                        "questionSubNumber": question_parts["questionSubNumber"],
                        "answer": answer,
                    }
                )

        return partitioned_answers

    def get_threshold_data(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive] = None,
    ) -> dict:
        if not isinstance(target_primitive, SF36):
            return {}

        return super(SF36QuestionnaireModule, self).get_threshold_data(
            target_primitive, module_config, primitives
        )

    def filter_results(
        self,
        primitives: list[Primitive],
        module_configs: list[ModuleConfig],
        is_for_user=False,
    ) -> list[Primitive]:
        if not primitives:
            return []

        if isinstance(primitives[0], SF36):
            return primitives

        return super(SF36QuestionnaireModule, self).filter_results(
            primitives, module_configs, is_for_user
        )
