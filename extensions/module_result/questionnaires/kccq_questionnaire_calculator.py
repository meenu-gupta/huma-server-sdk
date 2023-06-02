from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Primitive,
    KCCQ,
)
from extensions.module_result.module_result_utils import config_body_to_question_map
from extensions.module_result.questionnaires import SimpleScoreCalculator
from sdk.common.exceptions.exceptions import InvalidRequestException


class KCCQQuestionnaireCalculator(SimpleScoreCalculator):
    def calculate(self, primitive: Primitive, module_config: ModuleConfig):
        if not isinstance(primitive, KCCQ):
            return

        question_map = config_body_to_question_map(module_config.get_config_body())

        subscale_means = {
            KCCQ.SUBSCALE_PHYSICAL_LIMITATION: 0,
            KCCQ.SUBSCALE_SYMPTOM_STABILITY: 0,
            KCCQ.SUBSCALE_SYMPTOM_FREQUENCY: 0,
            KCCQ.SUBSCALE_SYMPTOM_BURDEN: 0,
            KCCQ.SUBSCALE_SELF_EFFICACY: 0,
            KCCQ.SUBSCALE_QUALITY_OF_LIFE: 0,
            KCCQ.SUBSCALE_SOCIAL_LIMITATION: 0,
        }
        for subscale, answers in primitive.partitioned_answers.items():
            mean = 0
            for answer in answers:
                weight = self._get_answer_weight(question_map, answer["answer"])
                mean += weight
            subscale_means[subscale] = mean / len(answers)

        primitive.physicalLimitation = (
            100 * (subscale_means[KCCQ.SUBSCALE_PHYSICAL_LIMITATION] - 1) / 4
        )

        primitive.symptomStability = (
            100 * (subscale_means[KCCQ.SUBSCALE_SYMPTOM_STABILITY] - 1) / 4
        )

        symptom_frequency_answers = []
        s3_answer = self._get_answer_by_question_number(
            primitive.partitioned_answers[KCCQ.SUBSCALE_SYMPTOM_FREQUENCY], 3
        )
        if s3_answer:
            symptom_frequency_answers.append(
                (self._get_answer_weight(question_map, s3_answer) - 1) / 4
            )

        s5_answer = self._get_answer_by_question_number(
            primitive.partitioned_answers[KCCQ.SUBSCALE_SYMPTOM_FREQUENCY], 5
        )
        if s5_answer:
            symptom_frequency_answers.append(
                (self._get_answer_weight(question_map, s5_answer) - 1) / 6
            )

        s7_answer = self._get_answer_by_question_number(
            primitive.partitioned_answers[KCCQ.SUBSCALE_SYMPTOM_FREQUENCY], 7
        )
        if s7_answer:
            symptom_frequency_answers.append(
                (self._get_answer_weight(question_map, s7_answer) - 1) / 6
            )

        s9_answer = self._get_answer_by_question_number(
            primitive.partitioned_answers[KCCQ.SUBSCALE_SYMPTOM_FREQUENCY], 9
        )
        if s9_answer:
            symptom_frequency_answers.append(
                (self._get_answer_weight(question_map, s9_answer) - 1) / 4
            )

        primitive.symptomFrequency = (
            100 * sum(symptom_frequency_answers) / len(symptom_frequency_answers)
        )

        primitive.symptomBurden = (
            100 * (subscale_means[KCCQ.SUBSCALE_SYMPTOM_BURDEN] - 1) / 4
        )

        primitive.totalSymptomScore = (
            primitive.symptomFrequency + primitive.symptomBurden
        ) / 2
        primitive.selfEfficacy = (
            100 * (subscale_means[KCCQ.SUBSCALE_SELF_EFFICACY] - 1) / 4
        )
        primitive.qualityOfLife = (
            100 * (subscale_means[KCCQ.SUBSCALE_QUALITY_OF_LIFE] - 1) / 4
        )
        primitive.socialLimitation = (
            100 * (subscale_means[KCCQ.SUBSCALE_SOCIAL_LIMITATION] - 1) / 4
        )

        primitive.overallSummaryScore = (
            primitive.physicalLimitation
            + primitive.totalSymptomScore
            + primitive.qualityOfLife
            + primitive.socialLimitation
        ) / 4

        primitive.clinicalSummaryScore = (
            primitive.physicalLimitation + primitive.totalSymptomScore
        ) / 2

    @staticmethod
    def _get_answer_by_question_number(subscale: list[dict], question_number: int):
        result = next(
            filter(lambda x: x["questionNumber"] == question_number, subscale), None
        )
        if result:
            return result["answer"]

    def _get_answer_weight(self, question_map, answer):
        question = question_map.get(answer.questionId)
        options = question.get("options", [])
        option = self._get_option_by_name(answer.answerText, options)
        if not option:
            msg = f"Answer {answer.answerText} is not an option"
            raise InvalidRequestException(msg)

        if "value" not in option:
            msg = f"The question {answer.questionId} doesn't have answer options configured with value"
            raise InvalidRequestException(msg)

        return option["weight"]
