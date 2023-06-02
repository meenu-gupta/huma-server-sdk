from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire
from .simple_score_calculator import SimpleScoreCalculator
from extensions.module_result.module_result_utils import config_body_to_question_map


class FJSScoreCalculator(SimpleScoreCalculator):
    def calculate(self, primitive: Questionnaire, module_config: ModuleConfig):
        question_map = config_body_to_question_map(module_config.get_config_body())
        scores = []
        for answer in primitive.answers:
            answer_weight = self._get_answer_weight(question_map, answer)
            scores.append(answer_weight)

        primitive.value = self._calculate_fjs_score(scores)

    def _calculate_fjs_score(self, scores: list):
        scores_count = len(scores)
        total_score = sum(scores)
        if scores_count < 12:
            total_score = self._calculate_mean_of_completed_answers(scores) * 12
        return 100 - ((total_score - 12) / 48 * 100)

    @staticmethod
    def _calculate_mean_of_completed_answers(scores: list) -> float:
        return sum(scores) / len(scores)
