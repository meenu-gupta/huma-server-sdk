from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import OACS
from extensions.module_result.questionnaires.simple_score_calculator import (
    SimpleScoreCalculator,
)
from sdk.common.utils.common_functions_utils import round_half_up


class OACSQuestionnaireCalculator(SimpleScoreCalculator):
    TOTAL_NUMBER_OF_QUESTIONS = 14

    def calculate(self, primitive: OACS, module_config: ModuleConfig):
        if not isinstance(primitive, OACS):
            return

        scoring_answers = primitive.scoring_answers
        skipped_question_score = 0
        calculated_score = sum(answer.answerScore for answer in scoring_answers)
        if (
            length_of_scoring_answer := len(scoring_answers)
        ) < self.TOTAL_NUMBER_OF_QUESTIONS:
            avg_score = calculated_score / length_of_scoring_answer
            if length_of_scoring_answer == self.TOTAL_NUMBER_OF_QUESTIONS - 2:
                skipped_question_score = 2 * avg_score
            elif length_of_scoring_answer == self.TOTAL_NUMBER_OF_QUESTIONS - 1:
                skipped_question_score = avg_score
        result = (calculated_score + skipped_question_score) / 28 * 50
        primitive.oacsScore = round_half_up(result, 1)
