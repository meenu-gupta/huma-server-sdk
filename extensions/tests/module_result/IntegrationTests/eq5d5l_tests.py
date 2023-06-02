from typing import Any
from extensions.module_result.models.primitives import Questionnaire, EQ5D5L
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireAnswer,
)
from extensions.module_result.modules import EQ5D5LModule
from extensions.tests.module_result.IntegrationTests.module_result_tests import (
    BaseModuleResultTest,
)
from extensions.module_result.questionnaires.eq5d_questionnaire_calculator import (
    EQ5DQuestionnaireCalculator,
)
from .test_samples import (
    sample_eq5d_questionnaire_result,
    sample_german_eq5d_questionnaire_result,
)


class EQ5D5LModuleTest(BaseModuleResultTest):
    def submit_eq5d(self, headers: dict[str, str], data: dict[str, Any]):
        return self.flask_client.post(
            f"{self.base_route}/{EQ5D5LModule.moduleId}", json=[data], headers=headers
        )

    def test_success_submit_and_retrieve_eq5d(self):
        rsp = self.submit_eq5d(self.headers, data=sample_eq5d_questionnaire_result())
        self.assertEqual(201, rsp.status_code)

        module_id = EQ5D5LModule.moduleId
        expected_index_value = 0.105
        expected_health_state = "13451"

        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search",
            json={"limit": 0, "skip": 0, "excludedFields": []},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        data = rsp.json
        eq5d5l_rsp = data[EQ5D5L.__name__][0]

        self.assertIn(Questionnaire.__name__, data)
        self.assertIn(EQ5D5L.__name__, data)
        for index, field in enumerate(EQ5DQuestionnaireCalculator.level_list[:-1]):
            self.assertEqual(eq5d5l_rsp[field], int(expected_health_state[index]))
        self.assertEqual(eq5d5l_rsp[EQ5D5L.EQ_VAS], 50)
        self.assertEqual(eq5d5l_rsp[EQ5D5L.HEALTH_STATE], int(expected_health_state))
        self.assertEqual(eq5d5l_rsp[EQ5D5L.INDEX_VALUE], expected_index_value)

    def test_success_submit_and_retrieve_eq5d_german(self):
        test_headers = {
            **self.headers,
            "x-hu-locale": "de",
        }
        rsp = self.submit_eq5d(
            headers=test_headers, data=sample_german_eq5d_questionnaire_result()
        )
        self.assertEqual(201, rsp.status_code)

        module_id = EQ5D5LModule.moduleId
        expected_index_value = 0.105
        expected_health_state = "13451"

        headers_with_english_language = {
            **self.headers,
            "x-hu-locale": "en",
        }
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search",
            json={"limit": 0, "skip": 0, "excludedFields": []},
            headers=headers_with_english_language,
        )
        self.assertEqual(200, rsp.status_code)

        data = rsp.json
        eq5d5l_rsp = data[EQ5D5L.__name__][0]

        self.assertIn(Questionnaire.__name__, data)
        self.assertIn(EQ5D5L.__name__, data)

        self.assertEqual(1, len(data["Questionnaire"]))
        self.assertEqual(
            "Please tap or drag on the scale to indicate how your health is TODAY.",
            data["Questionnaire"][0]["answers"][5][QuestionnaireAnswer.QUESTION],
        )

        for index, field in enumerate(EQ5DQuestionnaireCalculator.level_list[:-1]):
            self.assertEqual(eq5d5l_rsp[field], int(expected_health_state[index]))
        self.assertEqual(eq5d5l_rsp[EQ5D5L.EQ_VAS], 50)
        self.assertEqual(eq5d5l_rsp[EQ5D5L.HEALTH_STATE], int(expected_health_state))
        self.assertEqual(eq5d5l_rsp[EQ5D5L.INDEX_VALUE], expected_index_value)
