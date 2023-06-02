from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import OARS
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireAnswer,
)
from extensions.module_result.questionnaires.simple_score_calculator import (
    SimpleScoreCalculator,
)
from sdk.common.utils.common_functions_utils import round_half_up


class OARSQuestionnaireCalculator(SimpleScoreCalculator):
    TOTAL_NUMBER_OF_QUESTIONS = 14
    ANSWERS_MAX_VALUE = 4

    def calculate(self, primitive: OARS, module_config: ModuleConfig):
        if not isinstance(primitive, OARS):
            return

        scoring_answers = primitive.scoring_answers
        skipped_question_score = 0
        avg_score = 0

        calculated_score = sum(answer.answerScore for answer in scoring_answers)
        if (
            length_of_scoring_answer := len(scoring_answers)
        ) < self.TOTAL_NUMBER_OF_QUESTIONS:
            avg_score = calculated_score / length_of_scoring_answer
            if length_of_scoring_answer == self.TOTAL_NUMBER_OF_QUESTIONS - 2:
                skipped_question_score = 2 * avg_score
            elif length_of_scoring_answer == self.TOTAL_NUMBER_OF_QUESTIONS - 1:
                skipped_question_score = avg_score

        oars_score_ratio = (calculated_score + skipped_question_score) / (
            self.ANSWERS_MAX_VALUE * self.TOTAL_NUMBER_OF_QUESTIONS
        )
        primitive.oarsScore = round_half_up(oars_score_ratio * 100, 1)

        field_question_map = primitive.field_to_ids_map()
        primitive.sleepScore = self._calculate_domain_score(
            answers=scoring_answers,
            avg_score=avg_score,
            field_question_map=field_question_map,
            domain_field=primitive.SLEEP_SCORE,
        )
        primitive.mobilityScore = self._calculate_domain_score(
            answers=scoring_answers,
            avg_score=avg_score,
            field_question_map=field_question_map,
            domain_field=primitive.MOBILITY_SCORE,
        )
        primitive.nauseaScore = self._calculate_domain_score(
            answers=scoring_answers,
            avg_score=avg_score,
            field_question_map=field_question_map,
            domain_field=primitive.NAUSEA_SCORE,
        )
        primitive.painScore = self._calculate_domain_score(
            answers=scoring_answers,
            avg_score=avg_score,
            field_question_map=field_question_map,
            domain_field=primitive.PAIN_SCORE,
        )

    def _calculate_domain_score(
        self,
        answers: list[QuestionnaireAnswer],
        avg_score: float,
        domain_field: str,
        field_question_map: dict[str, set[str]],
    ):
        score = [
            answer.answerScore
            for answer in answers
            if answer.questionId in field_question_map[domain_field]
        ]
        questions_length = len(field_question_map[domain_field])
        if len(score) == questions_length - 2:
            score.extend([avg_score, avg_score])
        elif len(score) == questions_length - 1:
            score.append(avg_score)
        result = sum(score) / (questions_length * self.ANSWERS_MAX_VALUE) * 100
        return round_half_up(result, 1)
