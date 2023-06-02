import unittest

from extensions.export_deployment.helpers.convertion_helpers import (
    flat_text_choice_answer,
    flat_single_choice_answer,
    flat_boolean_answer,
    flat_text_answer,
    flat_scale_answer,
    flat_date_answer,
    flat_symptoms,
    flat_questionnaire,
    flat_numeric_answer,
)
from extensions.export_deployment.use_case.exportable.questionnaire_exportable_use_case import (
    QuestionnaireModuleExportableUseCase,
)
from extensions.module_result.models.primitives import Questionnaire
from extensions.tests.export_deployment.UnitTests.fixtures.questionnaire_fixtures import (
    sample_multiple_choice_question_with_comma,
    sample_answer_multiple_choice_question,
    sample_single_choice_question,
    sample_answer_single_question,
    sample_boolean_question,
    sample_answer_boolean_question,
    sample_text_question,
    sample_answer_text_question,
    sample_scale_question,
    sample_answer_scale_question,
    sample_date_question,
    sample_answer_date_question,
    sample_symptoms,
    sample_symptoms_result,
    sample_unknown_answer,
    sample_number_question,
    sample_answer_number_question,
    sample_multiple_choice_question_without_comma,
    sample_answer_multiple_choice_question_without_comma,
    sample_answer_multiple_choice_question_with_choices,
    sample_answer_single_question_with_choices,
    sample_answer_multiple_choice_question_without_any_selected,
    sample_baseline_questionnaire,
    sample_baseline_questionnaire_module_config,
    sample_splitted_baseline_questionnaire_answers,
)


class QuestionnaireTestCase(unittest.TestCase):
    sample_mcq = sample_multiple_choice_question_with_comma()
    sample_mcq_answer = sample_answer_multiple_choice_question()
    sample2_mcq_answer = sample_answer_multiple_choice_question()
    sample_scq = sample_single_choice_question()
    sample_scq_answer = sample_answer_single_question()
    sample_boolean = sample_boolean_question()
    sample_boolean_answer = sample_answer_boolean_question()
    sample_text = sample_text_question()
    sample_text_answer = sample_answer_text_question()
    sample_numeric = sample_number_question()
    sample_numeric_answer = sample_answer_number_question()
    sample_scale = sample_scale_question()
    sample_scale_answer = sample_answer_scale_question()
    sample_date = sample_date_question()
    sample_date_answer = sample_answer_date_question()

    def common_multiple_choice(self, answer):
        result = flat_text_choice_answer(self.sample_mcq, answer)
        question_text = answer["question"]
        long_choice_with_comma = (
            "Hoarseness (changes to the sound of your voice,"
            + " particularly becoming strained)"
        )

        self.assertEqual(result.get(f"{question_text} (Persistent cough)"), "selected")
        self.assertEqual(
            result.get(f"{question_text} ({long_choice_with_comma})"), "selected"
        )

        self.assertEqual(result.get(f"{question_text} (Other)"), "not selected")
        self.assertEqual(result.get(f"{question_text} (Not available)"), "selected")
        self.assertEqual(result.get(f"{question_text} (Not, available)"), "selected")
        self.assertEqual(
            result.get(f"{question_text} (Not, available, not)"), "selected"
        )

    def test_multiple_choice_question_with_choices(self):
        answer = sample_answer_multiple_choice_question_with_choices()
        result = flat_text_choice_answer(
            sample_multiple_choice_question_with_comma(), answer
        )
        question_text = answer["question"]
        long_choice_with_comma = (
            "Hoarseness (changes to the sound of your voice,"
            + " particularly becoming strained)"
        )

        self.assertEqual(result.get(f"{question_text} (Persistent cough)"), "selected")
        self.assertEqual(
            result.get(f"{question_text} ({long_choice_with_comma})"), "selected"
        )

        self.assertEqual(result.get(f"{question_text} (Other)"), "not selected")
        self.assertEqual(result.get(f"{question_text} (No symptoms)"), "selected")
        self.assertEqual(result.get(f"{question_text} (Sore throat)"), "selected")
        self.assertEqual(len(list(result)), 17)

    def test_multiple_choice_question_without_any_selected_choice(self):
        answer = sample_answer_multiple_choice_question_without_any_selected()
        result = flat_text_choice_answer(
            sample_multiple_choice_question_with_comma(), answer
        )
        for question, answer in result.items():
            self.assertEqual(answer, "not selected")
        self.assertEqual(len(list(result)), 17)

    def test_split_answer_choices(self):
        sample_questionnaire = sample_baseline_questionnaire().to_dict(
            include_none=False
        )
        initial_value = sample_baseline_questionnaire().to_dict(include_none=False)
        module_config = sample_baseline_questionnaire_module_config()
        QuestionnaireModuleExportableUseCase._split_answers(
            sample_questionnaire, module_config
        )
        self.assertNotEqual(initial_value, sample_questionnaire)
        answers = sample_questionnaire.get(Questionnaire.ANSWERS)
        self.assertEqual(sample_splitted_baseline_questionnaire_answers(), answers)

    def test_multiple_choice_question_no_comma(self):
        answer = sample_answer_multiple_choice_question_without_comma()
        result = flat_text_choice_answer(
            sample_multiple_choice_question_without_comma(), answer
        )
        question_text = answer["question"]
        self.assertEqual(result.get(f"{question_text} (Persistent cough)"), "selected")
        self.assertEqual(result.get(f"{question_text} (Fever)"), "selected")
        self.assertEqual(result.get(f"{question_text} (Sneezing)"), "not selected")
        self.assertEqual(len(list(result)), 3)

    def test_multiple_choice_question(self):
        self.common_multiple_choice(self.sample_mcq_answer)
        self.common_multiple_choice(self.sample2_mcq_answer)

    def test_single_choice_question(self):
        result = flat_single_choice_answer(self.sample_scq, self.sample_scq_answer)
        self.assertEqual(
            result.get(f"Please select that best describes your living situation"),
            "I live alone",
        )

    def test_single_choice_question_with_choices(self):
        result = flat_single_choice_answer(
            self.sample_scq, sample_answer_single_question_with_choices()
        )
        self.assertEqual(
            result.get(f"Please select that best describes your living situation"),
            "I live alone",
        )

    def test_boolean_question(self):
        result = flat_boolean_answer(self.sample_boolean, self.sample_boolean_answer)
        self.assertEqual(result.get(f"Have you had a test for COVID-19?"), "No")

    def test_text_question(self):
        result = flat_text_answer(self.sample_text, self.sample_text_answer)
        self.assertEqual(result.get(f"Please enter any other symptoms."), "Nothing")

    def test_numeric_question(self):
        result = flat_numeric_answer(self.sample_numeric, self.sample_numeric_answer)
        self.assertEqual(result.get(f"What is your age in years?"), "16.0")

    def test_scale_question(self):
        result = flat_scale_answer(self.sample_scale, self.sample_scale_answer)
        self.assertEqual(
            result.get(
                "In the last month, how frequently did you complete your scheduled"
                " medication and supplements routine?"
            ),
            "23",
        )

    def test_date_question(self):
        result = flat_date_answer(self.sample_date, self.sample_date_answer)
        self.assertEqual(
            result.get("When did your possible COVID-19 symptoms start?"), "2020-10-09"
        )

    def test_questionnaire(self):
        questionnaire = {
            "pages": [
                self.sample_scq,
                self.sample_mcq,
                self.sample_date,
                self.sample_text,
                self.sample_scale,
                self.sample_boolean,
                self.sample_numeric,
            ]
        }
        answers = [
            self.sample_boolean_answer,
            self.sample_scq_answer,
            self.sample_mcq_answer,
            self.sample_date_answer,
            self.sample_text_answer,
            self.sample_scale_answer,
            self.sample_numeric_answer,
            sample_unknown_answer(),
        ]
        result = flat_questionnaire(questionnaire, answers)

        question_text = self.sample_mcq_answer["question"]
        self.assertEqual(result.get(f"{question_text} (Other)"), "not selected")
        self.assertEqual(result.get(f"{question_text} (Not available)"), "selected")
        self.assertEqual(result.get(f"{question_text} (Not, available)"), "selected")
        self.assertEqual(
            result.get("When did your possible COVID-19 symptoms start?"), "2020-10-09"
        )
        self.assertEqual(
            result.get(
                "In the last month, how frequently did you complete your scheduled"
                " medication and supplements routine?"
            ),
            "23",
        )
        self.assertEqual(
            result.get(f"Please select that best describes your living situation"),
            "I live alone",
        )
        self.assertEqual(result.get(f"Have you had a test for COVID-19?"), "No")
        self.assertEqual(result.get(f"Please enter any other symptoms."), "Nothing")
        self.assertEqual(result.get(f"What is your age in years?"), "16.0")


class SymptomsTestCase(unittest.TestCase):
    sample_symptom = sample_symptoms()
    sample_symptom_result = sample_symptoms_result()

    def test_date_question(self):
        result = flat_symptoms(self.sample_symptom, self.sample_symptom_result)
        self.assertEqual(result.get("Sneezing"), "2")
        self.assertEqual(result.get("Loss of taste or smell"), "1")
        self.assertEqual(result.get("Other"), "1")
        self.assertEqual(result.get("Headache"), "not selected")


if __name__ == "__main__":
    unittest.main()
