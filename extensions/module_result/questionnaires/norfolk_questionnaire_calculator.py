import re
from typing import Union

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Primitive,
    NORFOLK,
    QuestionnaireAnswer,
)
from extensions.module_result.module_result_utils import config_body_to_question_map
from extensions.module_result.questionnaires import SimpleScoreCalculator
from extensions.utils import get_full_list
from sdk.common.exceptions.exceptions import InvalidRequestException


class NorfolkQuestionnaireCalculator(SimpleScoreCalculator):
    def calculate(self, primitive: Primitive, module_config: ModuleConfig):
        if not isinstance(primitive, NORFOLK):
            return

        question_map = config_body_to_question_map(module_config.get_config_body())
        question_number_to_value = self._get_question_number_to_value(
            question_map, primitive.answers
        )

        subscales = {
            NORFOLK.TOTAL_QOL_SCORE: ["18-52"],
            NORFOLK.PHYSICAL_FUNCTION_LARGER_FIBER: [25, 28, "30-32", 41, "44-52"],
            NORFOLK.ACTIVITIES_OF_DAILY_LIVING: [29, "39-40", 42, 43],
            NORFOLK.SYMPTOMS: ["18-24", 26],
            NORFOLK.SMALL_FIBER: [27, "33-35"],
            NORFOLK.AUTOMIC: ["36-38"],
        }

        for key, value in subscales.items():
            subscale_question_numbers = get_full_list(value)
            score = self._calculate_score(
                question_number_to_value, subscale_question_numbers
            )
            primitive.__setattr__(key, score)

    def _calculate_score(
        self, question_number_to_value: dict, subscale_question_numbers: list
    ) -> float:
        score = sum(
            [
                question_number_to_value.get(number) or 0
                for number in subscale_question_numbers
            ]
        )
        return float(score)

    def _get_question_number_to_value(
        self, question_map: dict, answers: list[QuestionnaireAnswer]
    ) -> dict:
        question_number_to_value = {}
        question_id_expr = re.compile(
            r"hu_norfolk_(?P<subscale>.*?)_q(?P<questionNumber>\d+)(?P<questionSubNumber>[a-z])*$"
        )

        for answer in answers:
            question_id_match = question_id_expr.match(answer.questionId)
            if not question_id_match:
                raise InvalidRequestException(
                    f"Wrong answer questionId format, it should be hu_norfolk_subscale_questionNumber[questionSubNumber]"
                )

            question_parts = question_id_match.groupdict()
            question_number = int(question_parts["questionNumber"])
            answer_weight = self._get_answer_weight(question_map, answer)
            question_number_to_value[question_number] = self._get_score(answer_weight)

        return question_number_to_value

    def _get_score(self, value: Union[int, list]):
        """If it is a MCQ and from the symptoms part of the questionnaire"""
        if isinstance(value, list):
            return 0 if 0 in value else 1
        return value

    def _get_answer_weight(self, question_map: dict, answer: QuestionnaireAnswer):
        question = question_map.get(answer.questionId)
        if question is None:
            raise InvalidRequestException(f"questionId {answer.questionId} is invalid")

        options = question.get("options")
        if not options:
            return

        answer_text = answer.answerText
        selection_criteria = question.get("selectionCriteria")
        if selection_criteria == "MULTIPLE":
            return [
                self._get_option_by_label(label, options, answer)
                for label in answer_text.split(",")
            ]

        return self._get_option_by_label(answer_text, options, answer)

    @staticmethod
    def _get_option_by_label(
        label: str, options: list[dict], answer: QuestionnaireAnswer
    ) -> int:
        option = next(filter(lambda x: x["label"] == label, options), None)
        if not option:
            msg = f"Answer {label} is not an option"
            raise InvalidRequestException(msg)

        if "weight" not in option:
            msg = f"The question {answer.questionId} doesn't have answer options configured with value"
            raise InvalidRequestException(msg)

        return option["weight"]
