import json
import logging
import re
from pathlib import Path

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import EQ5D5L, Questionnaire
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireAnswer,
)
from sdk.common.utils.validators import read_json_file
from .questionnaire_calculator import QuestionnaireCalculator
from extensions.module_result.module_result_utils import config_body_to_question_map

logger = logging.getLogger(__file__)


class EQ5DQuestionnaireCalculator(QuestionnaireCalculator):

    level_list = [
        EQ5D5L.MOBILITY,
        EQ5D5L.SELF_CARE,
        EQ5D5L.USUAL_ACTIVITIES,
        EQ5D5L.PAIN,
        EQ5D5L.ANXIETY,
        EQ5D5L.EQ_VAS,
    ]

    def calculate(self, primitive: EQ5D5L, module_config: ModuleConfig):

        if not isinstance(primitive, EQ5D5L):
            return

        eq5d5l_scores = self.build_eq5d5l_scores(
            config_body=module_config.configBody,
            answers=primitive.scoring_answers,
        )
        for key, value in eq5d5l_scores.items():
            setattr(primitive, key, value)

    @staticmethod
    def validate_option_values(raw_weights: dict):
        # Because our JSON schema validation isn't as robust as we'd like we allow
        # creating/saving questionnaires with invalid integer weights - usually empty strings.
        # Work around the problem by setting those weights to zero.
        weights = {}
        for label, weight in raw_weights.items():
            try:
                weights[label] = int(weight)
            except ValueError:
                logger.error("Zeroing invalid weight '%s' for answer %s", weight, label)
                weights[label] = 0

        return weights

    @staticmethod
    def find_index_value(score: int, region: str):
        root_path = Path(__file__).parent
        index_values = json.loads(
            read_json_file("fixtures/EQ-5D-5L_index_value.json", root_path)
        )
        try:
            return index_values[str(score)][region]
        except KeyError:
            logger.error("Index value %s or Region %s cannot be found", score, region)

    @staticmethod
    def _calculate_answer_score(answer: QuestionnaireAnswer, question: dict):
        raw_weights = {
            option["label"]: option["value"] for option in question["options"]
        }

        weights = EQ5DQuestionnaireCalculator.validate_option_values(raw_weights)
        answer.answerScore = 0

        # Splitting answerText on commas not followed by whitespace
        # It will work only if labels/answers have commas followed by whitespace
        for answerChoice in re.split(r",(?!\s)", answer.answerText):
            weight_score = weights.get(answerChoice)
            if weight_score:
                answer.answerScore += weight_score

    @classmethod
    def build_eq5d5l_scores(
        cls, config_body: dict, answers: list[QuestionnaireAnswer]
    ) -> dict[str, int]:

        question_map = config_body_to_question_map(config_body)
        if not question_map:
            logger.warning("Questionnaire had no questions")
        total_score = 0
        scores = dict()

        for index, answer in enumerate(answers[:6]):
            question = question_map.get(answer.questionId, None)
            if (
                question
                and question["format"] == "TEXTCHOICE"
                and "value" in question["options"][0]
            ):
                cls._calculate_answer_score(answer=answer, question=question)
                total_score += answer.answerScore * pow(10, 4 - index)
                answer_score = answer.answerScore

            else:
                try:
                    answer_score = answer.value or int(answer.answerText)
                except ValueError:
                    answer_score = 0
                    logger.warning(f"{answer.answerText} is not int type in {question}")

            scores[cls.level_list[index]] = answer_score
        total_score = int(total_score) or None  # to ignore extra answers
        if total_score:
            scores[EQ5D5L.HEALTH_STATE] = total_score
            scores[EQ5D5L.INDEX_VALUE] = cls.find_index_value(
                total_score, config_body["region"]
            )
        return scores


class DeprecatedEQ5DQuestionnaireCalculator(QuestionnaireCalculator):
    def calculate(self, primitive: Questionnaire, module_config: ModuleConfig):
        question_map = config_body_to_question_map(module_config.configBody)
        if not question_map:
            logger.warning(
                "Questionnaire %s had no questions", primitive.questionnaireId
            )
        total_score = None

        for index, answer in enumerate(primitive.answers):
            question = question_map.get(answer.questionId, None)
            if (
                question
                and question["format"] == "TEXTCHOICE"
                and "value" in question["options"][0]
            ):
                # We have a multi-choice question with weighted answers, add up the weights
                raw_weights = {
                    option["label"]: option["value"] for option in question["options"]
                }

                weights = self.validate_option_values(raw_weights)

                # If we have a total score already then preserve it.  If not set it to zero so we can accumulate
                # across all questions
                total_score = 0 if total_score is None else total_score
                answer.answerScore = 0

                # Splitting answerText on commas not followed by whitespace
                # It will work only if labels/answers have commas followed by whitespace
                for answerChoice in re.split(r",(?!\s)", answer.answerText):
                    weight_score = weights.get(answerChoice)
                    if weight_score:
                        answer.answerScore += weight_score

                total_score += answer.answerScore * pow(10, 4 - index)

        primitive.value = (
            self.find_index_value(total_score, module_config.configBody["region"])
            if total_score is not None
            else 0
        )

    @staticmethod
    def validate_option_values(raw_weights: dict):
        # Because our JSON schema validation isn't as robust as we'd like we allow
        # creating/saving questionnaires with invalid integer weights - usually empty strings.
        # Work around the problem by setting those weights to zero.
        weights = {}
        for label, weight in raw_weights.items():
            try:
                weights[label] = int(weight)
            except ValueError:
                logger.error("Zeroing invalid weight '%s' for answer %s", weight, label)
                weights[label] = 0

        return weights

    @staticmethod
    def find_index_value(score: int, region: str):
        root_path = Path(__file__).parent
        index_values = json.loads(
            read_json_file("fixtures/EQ-5D-5L_index_value.json", root_path)
        )
        try:
            return index_values[str(score)][region]
        except KeyError:
            logger.error("Index value %s or Region %s cannot be found", score, region)
            return 0
