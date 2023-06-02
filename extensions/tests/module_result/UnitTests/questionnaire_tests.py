from unittest import TestCase
from unittest.mock import MagicMock

from extensions.module_result.models.primitives import (
    Questionnaire,
    QuestionnaireAnswer,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionAnswerFormat,
)
from extensions.module_result.questionnaires.questionnaire_answer_validator import (
    QuestionnaireAnswerValidator,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    PrimitiveTestCase,
    COMMON_FIELDS,
)
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils.convertible import ConvertibleClassValidationError


def sample_answers():
    return [
        {
            QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
            QuestionnaireAnswer.QUESTION: "Please provide the date of your flu vaccine.",
            QuestionnaireAnswer.ANSWER_TEXT: "2019-06-30",
        },
        {
            QuestionnaireAnswer.QUESTION: "What is your waist and hip circumference?",
            QuestionnaireAnswer.QUESTION_ID: "composite_q1",
            QuestionnaireAnswer.COMPOSITE_ANSWER: {
                "waist_circumference": "100.1",
                "hip_circumference": "120.8",
            },
        },
    ]


def sample_questionnaire():
    questionnaire = {
        Questionnaire.QUESTIONNAIRE_ID: "questionnaire_id",
        Questionnaire.QUESTIONNAIRE_NAME: "Questionnaire",
        Questionnaire.ANSWERS: [
            {
                QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                QuestionnaireAnswer.QUESTION: "Please provide the date of your flu vaccine.",
                QuestionnaireAnswer.ANSWER_TEXT: "2019-06-30",
            },
            {
                QuestionnaireAnswer.QUESTION: "What is your waist and hip circumference?",
                QuestionnaireAnswer.QUESTION_ID: "composite_q1",
                QuestionnaireAnswer.COMPOSITE_ANSWER: {
                    "waist_circumference": "100.1",
                    "hip_circumference": "120.8",
                },
            },
        ],
    }
    questionnaire.update(COMMON_FIELDS)
    return questionnaire


def sample_multimedia_qustion_config():
    return {
        "pages": [
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "description",
                        "id": "5e94b2007773091c9a592651",
                        "required": True,
                        "format": "MEDIA",
                        "mediaType": ["PHOTO", "FILE", "VIDEO"],
                        "order": 1,
                        "text": "Question text",
                        "multipleAnswers": {
                            "enabled": True,
                            "maxAnswers": 2,
                        },
                    }
                ],
            }
        ]
    }


def sample_multimedia_asnwer():
    return {
        QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.MEDIA.value,
        QuestionnaireAnswer.QUESTION: "Upload a file",
        QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
        "filesList": [
            {
                "file": "5e94b2007773091c9a592651",
                "thumbnail": "5e94b2007773091c9a592651",
                "mediaType": "PHOTO",
            },
            {"file": "5e94b2007773091c9a592651", "mediaType": "FILE"},
        ],
    }


class QuestionnaireTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        questionnaire = sample_questionnaire()
        primitive = Questionnaire.create_from_dict(questionnaire, name="Questionnaire")
        self.assertIsNotNone(primitive)

    def test_success_missing_answer_text_and_answer_value(self):
        questionnaire = sample_questionnaire()
        questionnaire[Questionnaire.ANSWERS] = [
            {
                QuestionnaireAnswer.QUESTION: "What is your waist and hip circumference?",
                QuestionnaireAnswer.QUESTION_ID: "composite_q1",
            },
        ]

        res = Questionnaire.from_dict(questionnaire)
        self.assertIsNotNone(res)

    def test_failure_invalid_composite_answer(self):
        questionnaire = sample_questionnaire()
        questionnaire[Questionnaire.ANSWERS] = [
            {
                QuestionnaireAnswer.QUESTION: "What is your waist and hip circumference?",
                QuestionnaireAnswer.QUESTION_ID: "multiple_numeric_q1",
                QuestionnaireAnswer.COMPOSITE_ANSWER: "INVALID",
            },
        ]

        self._assert_convertible_validation_err(Questionnaire, questionnaire)

    def test_failure_without_required_fields(self):
        required_fields = {
            Questionnaire.QUESTIONNAIRE_ID,
            Questionnaire.QUESTIONNAIRE_NAME,
            Questionnaire.ANSWERS,
        }

        for field in required_fields:
            questionnaire = sample_questionnaire()
            del questionnaire[field]
            self._assert_convertible_validation_err(Questionnaire, questionnaire)


class QuestionnaireAnswerTestCase(TestCase):
    def test_no_validation_for_answers(self):
        answer = {
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXT.value,
            QuestionnaireAnswer.QUESTION: "What is your abdominal waist measurement (in cm)?",
            QuestionnaireAnswer.QUESTION_ID: "61b34a0b-d7b6-4488-ac82-7f6d18b5145e",
        }
        try:
            answer = QuestionnaireAnswer.from_dict(answer)
            QuestionnaireAnswer.validate(answer)
        except ConvertibleClassValidationError:
            self.fail()

    def test_media_answer_validator(self):
        config_body = sample_multimedia_qustion_config()
        answer = sample_multimedia_asnwer()
        try:
            answer = QuestionnaireAnswer.from_dict(answer)
            QuestionnaireAnswerValidator(
                questionnaire_config=config_body
            ).validate_answer(answer=answer)
        except ConvertibleClassValidationError:
            self.fail()

    def test_media_answer_validator_with_max_answer_exceed(self):
        config_body = sample_multimedia_qustion_config()
        config_body["pages"][0]["items"][0]["multipleAnswers"]["maxAnswers"] = 1
        answer = sample_multimedia_asnwer()
        answer = QuestionnaireAnswer.from_dict(answer)
        with self.assertRaises(InvalidRequestException):
            QuestionnaireAnswerValidator(
                questionnaire_config=config_body
            ).validate_answer(answer=answer)

    def test_media_answer_validator_with_wrong_media_type(self):
        config_body = sample_multimedia_qustion_config()
        config_body["pages"][0]["items"][0]["mediaType"] = ["VIDEO"]
        answer = sample_multimedia_asnwer()
        answer = QuestionnaireAnswer.from_dict(answer)
        with self.assertRaises(InvalidRequestException):
            QuestionnaireAnswerValidator(
                questionnaire_config=config_body
            ).validate_answer(answer=answer)
