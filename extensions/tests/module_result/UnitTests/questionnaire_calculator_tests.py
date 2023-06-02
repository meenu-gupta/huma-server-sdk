import unittest

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.module_result.questionnaires import (
    EQ5DQuestionnaireCalculator,
    DeprecatedEQ5DQuestionnaireCalculator,
)
from extensions.module_result.models.primitives import Questionnaire
from sdk.common.utils import inject


def sample_module_config():
    return ModuleConfig.from_dict(
        {
            "about": "string",
            "configBody": {
                "id": "b13403cb-f24e-4721-b362-9929bf0421ff",
                "isForManager": False,
                "region": "UK",
                "questionnaireType": "EQ5D_5L",
                "name": "EQ5D-5L",
                "pages": [
                    {
                        "type": "QUESTION",
                        "order": 1,
                        "items": [
                            {
                                "id": "b037104f-8c1d-42a7-bb94-851206b8f057",
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Your mobility TODAY",
                                "required": False,
                                "description": "Pick one",
                                "options": [
                                    {
                                        "label": "I have no problems in walking about",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "I have slight problems in walking about",
                                        "value": "2",
                                        "weight": 2,
                                    },
                                    {
                                        "label": "I have moderate problems in walking about",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                    {
                                        "label": "I have severe problems in walking about",
                                        "value": "4",
                                        "weight": 4,
                                    },
                                    {
                                        "label": "I am unable to walking about",
                                        "value": "5",
                                        "weight": 5,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                    },
                    {
                        "type": "QUESTION",
                        "order": 2,
                        "items": [
                            {
                                "id": "ace68441-6a3a-4ccd-9a26-8c37dc3273d9",
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Your self-care TODAY",
                                "required": True,
                                "description": "Pick one",
                                "options": [
                                    {
                                        "label": "I have no problems washing or dressing myself",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "I have slight problems washing or dressing myself",
                                        "value": "2",
                                        "weight": 2,
                                    },
                                    {
                                        "label": "I have moderate problems washing or dressing myself",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                    {
                                        "label": "I have severe problems washing or dressing myself",
                                        "value": "4",
                                        "weight": 4,
                                    },
                                    {
                                        "label": "I am unable to wash or dress myself",
                                        "value": "5",
                                        "weight": 5,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                    },
                    {
                        "type": "QUESTION",
                        "order": 3,
                        "items": [
                            {
                                "id": "dc5632b4-2ce7-4b72-b187-e4f8f777a94a",
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Your usual activities TODAY",
                                "required": True,
                                "description": "Pick one",
                                "options": [
                                    {
                                        "label": "I have no problems doing my usual activities",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "I have slight problems doing my usual activities",
                                        "value": "2",
                                        "weight": 2,
                                    },
                                    {
                                        "label": "I have moderate problems doing my usual activities",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                    {
                                        "label": "I have severe problems doing my usual activities",
                                        "value": "4",
                                        "weight": 4,
                                    },
                                    {
                                        "label": "I am unable to do my usual activities",
                                        "value": "5",
                                        "weight": 5,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                    },
                    {
                        "type": "QUESTION",
                        "order": 4,
                        "items": [
                            {
                                "id": "647a6dc7-2289-4988-8451-c791c72b924f",
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Your pain/discomfort TODAY",
                                "required": True,
                                "description": "Pick one",
                                "options": [
                                    {
                                        "label": "I have no pain or discomfort",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "I have slight pain or discomfort",
                                        "value": "2",
                                        "weight": 2,
                                    },
                                    {
                                        "label": "I have moderate pain or discomfort",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                    {
                                        "label": "I have severe pain or discomfort",
                                        "value": "4",
                                        "weight": 4,
                                    },
                                    {
                                        "label": "I have extreme pain or discomfort",
                                        "value": "5",
                                        "weight": 5,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                    },
                    {
                        "type": "QUESTION",
                        "order": 5,
                        "items": [
                            {
                                "id": "0cc66b89-108e-44d2-966a-e3a7be63bd63",
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Your anxiety/depression TODAY",
                                "required": True,
                                "description": "Pick one",
                                "options": [
                                    {
                                        "label": "I'm not anxious or pressed",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "I'm slightly anxious or pressed",
                                        "value": "2",
                                        "weight": 2,
                                    },
                                    {
                                        "label": "I'm moderately anxious or pressed",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                    {
                                        "label": "I'm severely anxious or pressed",
                                        "value": "4",
                                        "weight": 4,
                                    },
                                    {
                                        "label": "I'm extremely anxious or pressed",
                                        "value": "5",
                                        "weight": 5,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                    },
                ],
            },
            "moduleId": "Questionnaire",
            "moduleName": "Questionnaire",
            "status": "ENABLED",
        }
    )


class QuestionnaireCalculatorTest(
    unittest.TestCase
):  # Would need to refactor this use Simple Calculator
    def setUp(self) -> None:
        def bind(binder):
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(bind)

    def test_eq5_valid_raw_weights(self):
        weights = EQ5DQuestionnaireCalculator.validate_option_values(
            {"a": "1", "b": "2"}
        )
        self.assertEqual({"a": 1, "b": 2}, weights)

    def test_eq5_invalid_raw_weights(self):
        weights = EQ5DQuestionnaireCalculator.validate_option_values(
            {"a": "a", "b": "2"}
        )
        self.assertEqual({"a": 0, "b": 2}, weights)

    def test_deprecated_eq5_valid_raw_weights(self):
        weights = DeprecatedEQ5DQuestionnaireCalculator.validate_option_values(
            {"a": "1", "b": "2"}
        )
        self.assertEqual({"a": 1, "b": 2}, weights)

    def test_deprecated_eq5_invalid_raw_weights(self):
        weights = DeprecatedEQ5DQuestionnaireCalculator.validate_option_values(
            {"a": "a", "b": "2"}
        )
        self.assertEqual({"a": 0, "b": 2}, weights)

    def test_deprecated_eq5_valid_questionnaire_result(self):
        questionnaire_result = Questionnaire.from_dict(
            {
                "moduleId": "Questionnaire",
                "userId": "5e8f0c74b50aa9656c34789c",
                "deploymentId": "5e8f0c74b50aa9656c34789c",
                "deviceName": "iOS",
                "answers": [
                    {
                        "questionId": "b037104f-8c1d-42a7-bb94-851206b8f057",
                        "question": "Your mobility TODAY",
                        "answerText": "I have no problems in walking about",
                    },
                    {
                        "questionId": "ace68441-6a3a-4ccd-9a26-8c37dc3273d9",
                        "question": "Your self-care TODAY",
                        "answerText": "I have moderate problems washing or dressing myself",
                    },
                    {
                        "questionId": "dc5632b4-2ce7-4b72-b187-e4f8f777a94a",
                        "question": "Your usual activities TODAY",
                        "answerText": "I have severe problems doing my usual activities",
                    },
                    {
                        "questionId": "647a6dc7-2289-4988-8451-c791c72b924f",
                        "question": "Your pain/discomfort TODAY",
                        "answerText": "I have extreme pain or discomfort",
                    },
                    {
                        "questionId": "0cc66b89-108e-44d2-966a-e3a7be63bd63",
                        "question": "Your anxiety/depression TODAY",
                        "answerText": "I'm extremely anxious or pressed",
                    },
                ],
                "questionnaireId": "b13403cb-f24e-4721-b362-9929bf0421ff",
                "questionnaireName": "Questionnaire",
            }
        )

        DeprecatedEQ5DQuestionnaireCalculator().calculate(
            questionnaire_result, sample_module_config()
        )
        self.assertEqual(-0.131, questionnaire_result.value)

    def test_questionnaire_result_without_answers(self):
        questionnaire_result = Questionnaire.from_dict(
            {
                "moduleId": "Questionnaire",
                "userId": "5e8f0c74b50aa9656c34789c",
                "deploymentId": "5e8f0c74b50aa9656c34789c",
                "deviceName": "iOS",
                "answers": [],
                "questionnaireId": "b13403cb-f24e-4721-b362-9929bf0421ff",
                "questionnaireName": "Questionnaire",
            }
        )

        DeprecatedEQ5DQuestionnaireCalculator().calculate(
            questionnaire_result, sample_module_config()
        )
        self.assertEqual(0, questionnaire_result.value)

    def test_questionnaire_result_with_incorrect_number_of_answers(self):
        questionnaire_result = Questionnaire.from_dict(
            {
                "moduleId": "Questionnaire",
                "userId": "5e8f0c74b50aa9656c34789c",
                "deploymentId": "5e8f0c74b50aa9656c34789c",
                "deviceName": "iOS",
                "answers": [
                    {
                        "questionId": "b037104f-8c1d-42a7-bb94-851206b8f057",
                        "question": "Your mobility TODAY",
                        "answerText": "I have no problems in walking about",
                    }
                ],
                "questionnaireId": "b13403cb-f24e-4721-b362-9929bf0421ff",
                "questionnaireName": "Questionnaire",
            }
        )

        DeprecatedEQ5DQuestionnaireCalculator().calculate(
            questionnaire_result, sample_module_config()
        )
        self.assertEqual(0, questionnaire_result.value)
