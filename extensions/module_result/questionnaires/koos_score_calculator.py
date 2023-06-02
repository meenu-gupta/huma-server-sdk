from copy import copy

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Primitive,
    Questionnaire,
    KOOS,
    WOMAC,
)
from extensions.module_result.module_result_utils import config_body_to_question_map
from extensions.module_result.questionnaires import SimpleScoreCalculator

ADL = KOOS.ADL_PREFIX
PAIN = KOOS.PAIN_PREFIX
SYMPTOMS = KOOS.SYMPTOM_PREFIX
SPORT_RECREATION = KOOS.SPORT_RECREATION_PREFIX
QUALITY_OF_LIFE = KOOS.QUALITY_OF_LIFE_PREFIX


class KOOSQuestionnaireCalculator(SimpleScoreCalculator):
    scores = {}

    def calculate(self, primitive: Primitive, module_config: ModuleConfig):
        if isinstance(primitive, Questionnaire):
            self.scores.clear()
            question_map = config_body_to_question_map(module_config.get_config_body())
            for answer in primitive.answers:
                answer_weight = self._get_answer_weight(question_map, answer)
                self.scores[answer.questionId] = answer_weight

        elif isinstance(primitive, KOOS):
            koos_data = self._calculate_koos(self.scores)
            for key, value in koos_data.items():
                primitive.__setattr__(key, value)

        elif isinstance(primitive, WOMAC):
            womac_data = self._calculate_womac(self.scores)
            for key, value in womac_data.items():
                primitive.__setattr__(key, value)

    def _calculate_koos(self, answers: dict) -> dict:
        scores = {
            ADL: 0,
            PAIN: 0,
            SYMPTOMS: 0,
            SPORT_RECREATION: 0,
            QUALITY_OF_LIFE: 0,
        }
        occurrences = copy(scores)
        score_with_field_mapping = {
            KOOS.PAIN_SCORE: PAIN,
            KOOS.ADL_SCORE: ADL,
            KOOS.SYMPTOMS_SCORE: SYMPTOMS,
            KOOS.SPORT_RECREATION_SCORE: SPORT_RECREATION,
            KOOS.QUALITY_OF_LIFE_SCORE: QUALITY_OF_LIFE,
        }

        for answer in answers:
            for key in scores:
                if answer.startswith(key):
                    scores[key] += answers[answer]
                    occurrences[key] += 1
                    break

        return {
            k: self._calculate_koos_with_formula(scores[v], occurrences[v])
            for k, v in score_with_field_mapping.items()
        }

    @staticmethod
    def _calculate_koos_with_formula(score: int, occurrences: int) -> float:
        return 100 - score / occurrences * 100 / 4

    @staticmethod
    def _calculate_womac(answers: dict) -> dict:
        scores = {
            PAIN: 0,
            SYMPTOMS: 0,
            ADL: 0,
        }
        pain_suffixes = (
            "_flat_surface",
            "_going_updown",
            "_at_night",
            "_sitting_lying",
            "_upright",
        )
        symptoms_suffixes = (
            "_wakening",
            "_sitting",
        )
        for answer in answers:
            if answer.startswith(ADL):
                scores[ADL] += answers[answer]

            elif answer.startswith(PAIN) and answer.endswith(pain_suffixes):
                scores[PAIN] += answers[answer]

            elif answer.startswith(SYMPTOMS) and answer.endswith(symptoms_suffixes):
                scores[SYMPTOMS] += answers[answer]

        pain_score = 100 - scores[PAIN] * 100 / 20
        symptoms_score = 100 - scores[SYMPTOMS] * 100 / 8
        adl_score = 100 - scores[ADL] * 100 / 68

        return {
            WOMAC.PAIN_SCORE: pain_score,
            WOMAC.SYMPTOMS_SCORE: symptoms_score,
            WOMAC.ADL_SCORE: adl_score,
            WOMAC.TOTAL_SCORE: sum([pain_score, symptoms_score, adl_score]) / 3,
        }
