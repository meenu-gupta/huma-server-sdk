from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire
from extensions.module_result.module_result_utils import config_body_to_question_map
from sdk.common.exceptions.exceptions import InvalidRequestException
from .questionnaire_calculator import QuestionnaireCalculator


class SimpleScoreCalculator(QuestionnaireCalculator):
    def calculate(self, primitive: Questionnaire, module_config: ModuleConfig):
        question_map = config_body_to_question_map(module_config.get_config_body())
        total_score = 0
        for answer in primitive.answers:
            question = question_map.get(answer.questionId)
            options = question.get("options", [])
            option = self._get_option_by_name(answer.answerText, options)
            if not option:
                msg = f"Answer {answer.answerText} is not an option"
                raise InvalidRequestException(msg)

            answer.answerScore = option.get("weight", 0)
            total_score += answer.answerScore

        module_config_body = module_config.get_config_body()
        max_score = module_config_body.get("maxScore")
        reverse_calculation = module_config_body.get("reverseCalculation")

        if max_score and reverse_calculation:
            primitive.value = max_score - total_score
        else:
            primitive.value = total_score

    @staticmethod
    def _get_option_by_name(name: str, options: list[dict]):
        return next(filter(lambda x: x["label"] == name, options), None)

    def _get_answer_weight(self, question_map, answer):
        question = question_map.get(answer.questionId)
        options = question.get("options", [])
        option = self._get_option_by_name(answer.answerText, options)
        if not option:
            msg = f"Answer {answer.answerText} is not an option"
            raise InvalidRequestException(msg)

        if "weight" not in option:
            msg = f"The question {answer.questionId} doesn't have answer options configured with value"
            raise InvalidRequestException(msg)

        return option["weight"]
