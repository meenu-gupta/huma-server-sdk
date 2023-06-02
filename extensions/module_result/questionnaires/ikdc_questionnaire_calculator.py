from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import IKDC
from extensions.module_result.module_result_utils import get_maximum_possible_score
from extensions.module_result.questionnaires import SimpleScoreCalculator


class IKDCQuestionnaireCalculator(SimpleScoreCalculator):
    minimumAnswered = 16

    def calculate(self, primitive: IKDC, module_config: ModuleConfig):
        if not isinstance(primitive, IKDC):
            return

        scoring_answers = primitive.scoring_answers
        calculated_score = sum(answer.answerScore for answer in scoring_answers)
        maximum_score = get_maximum_possible_score(
            module_config.get_config_body(),
            set(answer.questionId for answer in scoring_answers),
        )
        primitive.value = (calculated_score / maximum_score) * 100
