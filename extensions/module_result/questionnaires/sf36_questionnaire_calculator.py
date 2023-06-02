from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Primitive, SF36
from extensions.module_result.module_result_utils import config_body_to_question_map
from extensions.module_result.questionnaires import SimpleScoreCalculator


class SF36QuestionnaireCalculator(SimpleScoreCalculator):
    def calculate(self, primitive: Primitive, module_config: ModuleConfig):
        if not isinstance(primitive, SF36):
            return

        question_map = config_body_to_question_map(module_config.get_config_body())
        subscale_means = {
            SF36.SUBSCALE_GENERAL_HEALTH: None,
            SF36.SUBSCALE_PAIN: None,
            SF36.SUBSCALE_SOCIAL_FUNCTIONING: None,
            SF36.SUBSCALE_EMOTIONAL_WELL_BEING: None,
            SF36.SUBSCALE_ENERGY_FATIGUE: None,
            SF36.SUBSCALE_LIMITATIONS_EMOTIONAL_PROBLEMS: None,
            SF36.SUBSCALE_LIMITATIONS_PHYSICAL_HEALTH: None,
            SF36.SUBSCALE_PHYSICAL_FUNCTIONING: None,
        }
        for subscale, answers in primitive.answers.items():
            total = 0
            for answer in answers:
                weight = self._get_answer_weight(question_map, answer["answer"])
                total += weight
            mean = total / len(answers)
            subscale_means[subscale] = mean

        primitive.generalHealthScore = subscale_means[SF36.SUBSCALE_GENERAL_HEALTH]
        primitive.painScore = subscale_means[SF36.SUBSCALE_PAIN]
        primitive.socialFunctioningScore = subscale_means[
            SF36.SUBSCALE_SOCIAL_FUNCTIONING
        ]
        primitive.emotionalWellBeingScore = subscale_means[
            SF36.SUBSCALE_EMOTIONAL_WELL_BEING
        ]
        primitive.energyFatigueScore = subscale_means[SF36.SUBSCALE_ENERGY_FATIGUE]
        primitive.limitationsEmotionalProblemsScore = subscale_means[
            SF36.SUBSCALE_LIMITATIONS_EMOTIONAL_PROBLEMS
        ]
        primitive.limitationsPhysicalHealthScore = subscale_means[
            SF36.SUBSCALE_LIMITATIONS_PHYSICAL_HEALTH
        ]
        primitive.physicalFunctioningScore = subscale_means[
            SF36.SUBSCALE_PHYSICAL_FUNCTIONING
        ]

    def _get_answer_weight(self, question_map, answer):
        question = question_map.get(answer.questionId)
        if question["format"] == "BOOLEAN":
            return 100 if answer.answerText == "No" else 0

        return super()._get_answer_weight(question_map, answer)
