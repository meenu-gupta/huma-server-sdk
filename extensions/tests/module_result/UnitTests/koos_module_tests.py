import unittest

from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    WOMAC,
    KOOS,
    Questionnaire,
    QuestionnaireAnswer,
)
from extensions.module_result.modules import KOOSQuestionnaireModule
from extensions.module_result.questionnaires.koos_score_calculator import (
    KOOSQuestionnaireCalculator,
)


class KoosModuleTestCase(unittest.TestCase):
    @staticmethod
    def _sample_answers():
        return {
            "koos_pain_flat_surface": 1,
            "koos_pain_activities": 1,
            "koos_pain_straightening": 1,
            "koos_pain_bending": 1,
            "koos_pain_experience": 1,
            "koos_symptom_wakening": 2,
            "koos_symptom_sitting": 1,
            "koos_symptom_knee_hangup": 1,
            "koos_symptom_knee_straighten": 2,
            "koos_function_standing": 2,
            "koos_function_pickup_object": 2,
            "koos_function_flat_surface": 2,
            "koos_function_shopping": 2,
            "koos_function_stockings": 2,
            "koos_function_rising_bed": 2,
            "koos_function_descending_stairs": 2,
            "koos_function_ascending_stairs": 2,
            "koos_function_rising": 2,
            "koos_sports_squatting": 2,
            "koos_sports_running": 2,
            "koos_sports_jumping": 2,
            "koos_quality_often_aware": 1,
            "koos_quality_modified_lifestyle": 1,
        }

    @staticmethod
    def _sample_config_body():
        return {
            "id": "koos_configbody",
            "isForManager": False,
            "name": "KOOS Knee Survey",
            "pages": [
                {
                    "items": [
                        {
                            "description": "",
                            "format": "TEXTCHOICE",
                            "id": "koos_symptom_knee_swelling",
                            "logic": {"isEnabled": False},
                            "options": [
                                {"label": "Never", "value": "0", "weight": 0},
                            ],
                            "order": 1,
                            "required": False,
                            "selectionCriteria": "SINGLE",
                            "text": "Do you have swelling in your knee?",
                        }
                    ],
                    "order": 3,
                    "type": "QUESTION",
                },
                {
                    "items": [
                        {
                            "description": "",
                            "format": "TEXTCHOICE",
                            "id": "koos_symptom_knee_noise",
                            "logic": {"isEnabled": False},
                            "options": [
                                {"label": "Never", "value": "0", "weight": 0},
                            ],
                            "order": 1,
                            "required": False,
                            "selectionCriteria": "SINGLE",
                            "text": "Do you feel grinding, hear clicking or any other type of noise when your knee moves?",
                        }
                    ],
                    "order": 4,
                    "type": "QUESTION",
                },
                {
                    "items": [
                        {
                            "description": "",
                            "format": "TEXTCHOICE",
                            "id": "koos_symptom_knee_hangup",
                            "logic": {"isEnabled": False},
                            "options": [
                                {"label": "Never", "value": "0", "weight": 0},
                            ],
                            "order": 1,
                            "required": False,
                            "selectionCriteria": "SINGLE",
                            "text": "Does your knee catch or hang up when moving?",
                        }
                    ],
                    "order": 5,
                    "type": "QUESTION",
                },
            ],
        }

    @staticmethod
    def _answers():
        return [
            {
                "answerText": "Never",
                "question": "Do you have swelling in your knee?",
                "questionId": "koos_symptom_knee_swelling",
                "format": "TEXTCHOICE",
            },
            {
                "answerText": "Never",
                "question": "Do you feel grinding, hear clicking or any other type of noise when your knee moves?",
                "questionId": "koos_symptom_knee_noise",
                "format": "TEXTCHOICE",
            },
            {
                "answerText": "Never",
                "question": "Does your knee catch or hang up when moving?",
                "questionId": "koos_symptom_knee_hangup",
                "format": "TEXTCHOICE",
            },
        ]

    def test_success_calculate_koos_with_formula(self):
        calculator = KOOSQuestionnaireCalculator()
        res = calculator._calculate_koos_with_formula(10, 4)
        self.assertEqual(res, 37.5)

    def test_success_calculate_womac_score(self):
        calculator = KOOSQuestionnaireCalculator()
        res = calculator._calculate_womac(self._sample_answers())
        self.assertEqual(res[WOMAC.PAIN_SCORE], 95.0)
        self.assertEqual(res[WOMAC.SYMPTOMS_SCORE], 62.5)
        self.assertEqual(res[WOMAC.ADL_SCORE], 73.52941176470588)
        self.assertEqual(res[WOMAC.TOTAL_SCORE], 77.00980392156863)

    def test_success_calculate_koos_score(self):
        calculator = KOOSQuestionnaireCalculator()
        res = calculator._calculate_koos(self._sample_answers())
        self.assertEqual(res[KOOS.PAIN_SCORE], 75.0)
        self.assertEqual(res[KOOS.SYMPTOMS_SCORE], 62.5)
        self.assertEqual(res[KOOS.SPORT_RECREATION_SCORE], 50.0)
        self.assertEqual(res[KOOS.ADL_SCORE], 50.0)
        self.assertEqual(res[KOOS.QUALITY_OF_LIFE_SCORE], 75.0)

    def test_failure_calculate_score_not_enough_answered_questions(self):
        module = KOOSQuestionnaireModule()
        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module._check_answered_required_questions(["koos_pain_flat_surface"])

    def test_removing_previously_not_skipped_questions(self):
        module = KOOSQuestionnaireModule()
        module._config = ModuleConfig(configBody=self._sample_config_body())
        answers = self._answers()
        primitive = Questionnaire(answers=[QuestionnaireAnswer(**q) for q in answers])
        module.calculate(primitive)
        self.assertEqual(len(answers), len(KOOSQuestionnaireCalculator.scores))

        module = KOOSQuestionnaireModule()
        module._config = ModuleConfig(configBody=self._sample_config_body())
        answers = self._answers()[::2]
        primitive = Questionnaire(answers=[QuestionnaireAnswer(**q) for q in answers])
        module.calculate(primitive)
        self.assertEqual(len(answers), len(KOOSQuestionnaireCalculator.scores))


if __name__ == "__main__":
    unittest.main()
