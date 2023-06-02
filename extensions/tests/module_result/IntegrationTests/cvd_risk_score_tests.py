from unittest.mock import patch

from bson import ObjectId

from extensions.authorization.models.user import User
from extensions.module_result.common.enums import BiologicalSex
from extensions.module_result.models.primitives import (
    Questionnaire,
    QuestionnaireAnswer,
    CVDRiskScore,
)
from extensions.module_result.models.primitives.cvd_risk_score import RiskLabel
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionAnswerFormat,
    QuestionAnswerSelectionCriteria,
)
from extensions.module_result.modules.cvd_risk_score.ai_cvd_model import (
    CVDRiskScoreRequestObject,
    CVDRiskScoreResponseObject,
)
from extensions.module_result.modules.cvd_risk_score.service import AIScoringService
from extensions.tests.module_result.IntegrationTests.module_result_tests import (
    BaseModuleResultTest,
)
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_cvd_risk_score_questionnaire,
    sample_heart_rate,
    sample_body_measurement,
)


VALID_USER_ID = "5e8f0c74b50aa9656c34789c"
SERVICE_PATH = (
    "extensions.module_result.modules.cvd_risk_score._calculator.AIScoringService"
)
AI_SCORE_RESPONSE_DATA = {
    "risk": 0.2019456137,
    CVDRiskScore.RISK_FACTORS: [
        {"contribution": 0.4103573787, "label": "Being a smoker"},
        {"contribution": 0.2665759083, "label": "Self-rated health"},
        {
            "contribution": 0.2602712645,
            "label": "Sibling diagnosed with heart disease",
        },
        {
            "contribution": 0.1687113961,
            "label": "Father diagnosed with heart disease",
        },
        {"contribution": 0.0623476315, "label": "Hip circumference"},
        {"contribution": 0.0570181849, "label": "Waist-to-hip ratio"},
        {"contribution": -0.0830142082, "label": "Good sleep duration"},
    ],
    CVDRiskScore.RISK_TRAJECTORY: [
        {"risk": 0.0062371738, "days": 182.5},
        {"risk": 0.0130086433, "days": 365.0},
        {"risk": 0.0281641166, "days": 730.0},
        {"risk": 0.0452726514, "days": 1095.0},
        {"risk": 0.064112053, "days": 1460.0},
        {"risk": 0.0837740127, "days": 1825.0},
        {"risk": 0.1052018971, "days": 2190.0},
        {"risk": 0.1284747656, "days": 2555.0},
        {"risk": 0.152093274, "days": 2920.0},
        {"risk": 0.1770228313, "days": 3285.0},
        {"risk": 0.2019456137, "days": 3650.0},
    ],
}


class AIMockService(AIScoringService):
    def get_cvd_risk_score(
        self, data: CVDRiskScoreRequestObject
    ) -> CVDRiskScoreResponseObject:
        data = AI_SCORE_RESPONSE_DATA
        return self.build_response_object(data)


class CVDRiskScoreTestCase(BaseModuleResultTest):
    def setUp(self):
        super(CVDRiskScoreTestCase, self).setUp()
        self.url = f"{self.base_route}/CVDRiskScore"
        self.headers.update(self.get_headers_for_token(VALID_USER_ID))

    def test_submit_cdv_risk_score(self):
        expected_number_of_primitives = 4
        rsp = self.submit_result()
        self.assertEqual(201, rsp.status_code)
        self.assertNotIn("errors", rsp.json)

        response = self.search_cvd_primitives().json
        created_primitives = len(response.keys())
        risk_factors = response[CVDRiskScore.__name__][1][CVDRiskScore.RISK_FACTORS]
        possible_risk_factors = {
            f.value for f in RiskLabel if f.value != RiskLabel.ALCOHOL.value
        }
        actual_risk_factors = {f["name"] for f in risk_factors}

        self.assertEqual(possible_risk_factors, actual_risk_factors)
        self.assertNotIn(RiskLabel.ALCOHOL.value, actual_risk_factors)
        self.assertEqual(
            expected_number_of_primitives,
            created_primitives,
            msg="Not all primitives were created",
        )

    def test_support_for_previous_deployment_with_alcohol_risk_factor(self):

        response = self.search_cvd_primitives().json
        # existing CVDRisk Score
        risk_factors = response[CVDRiskScore.__name__][0][CVDRiskScore.RISK_FACTORS]
        possible_risk_factors = {f.value for f in RiskLabel}
        actual_risk_factors = {f["name"] for f in risk_factors}

        self.assertEqual(possible_risk_factors, actual_risk_factors)
        self.assertIn(RiskLabel.ALCOHOL.value, actual_risk_factors)

    def test_success_submit_cdv_when_first_primitive_not_questionnaire(self):
        json = [
            sample_heart_rate(),
            sample_body_measurement(),
            sample_cvd_risk_score_questionnaire(),
        ]
        rsp = self.submit_result(json=json)
        self.assertEqual(201, rsp.status_code)
        self.assertNotIn("errors", rsp.json)

    def test_failure_submit_cdv_risk_score_no_biological_sex(self):
        self.unset_user_field(field=User.BIOLOGICAL_SEX)
        rsp = self.submit_result()
        self.assertEqual(403, rsp.status_code)

    def test_submit_cdv_risk_score_no_biological_sex__sex_in_body(self):
        self.unset_user_field(field=User.BIOLOGICAL_SEX)

        primitive = sample_cvd_risk_score_questionnaire()
        sex_answer = {
            QuestionnaireAnswer.QUESTION_ID: "cvd_sex",
            QuestionnaireAnswer.QUESTION: "What is you biologicalSex?",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.SINGLE.value,
            QuestionnaireAnswer.CHOICES: [i.name for i in BiologicalSex],
            QuestionnaireAnswer.SELECTED_CHOICES: [BiologicalSex.MALE.name],
        }
        primitive[Questionnaire.ANSWERS].append(sex_answer)
        rsp = self.submit_result(json=[primitive])
        self.assertEqual(201, rsp.status_code)
        self.assertNotIn("errors", rsp.json)

    def test_submit_cvd_risk_score_no_age(self):
        self.unset_user_field(field=User.DATE_OF_BIRTH)
        rsp = self.submit_result()
        self.assertEqual(403, rsp.status_code)

    @patch("requests.post")
    def test_request_id_in_header_cvd_score_submit(self, fake_post):
        json = [
            sample_cvd_risk_score_questionnaire(),
            sample_heart_rate(),
            sample_body_measurement(),
        ]
        request_id = "34444drf"
        self.headers["x-request-id"] = request_id
        fake_post.return_value.json.return_value = AI_SCORE_RESPONSE_DATA
        self.flask_client.post(self.url, json=json, headers=self.headers)
        kwargs = fake_post.call_args.kwargs
        self.assertEqual(kwargs["headers"]["x-request-id"], request_id)

    @patch(SERVICE_PATH, AIMockService)
    def submit_result(self, json=None):
        json = json or [
            sample_cvd_risk_score_questionnaire(),
            sample_heart_rate(),
            sample_body_measurement(),
        ]
        return self.flask_client.post(self.url, json=json, headers=self.headers)

    def search_cvd_primitives(self):
        url = f"{self.url}/search"
        return self.flask_client.post(url, headers=self.headers)

    def unset_user_field(self, field):
        self.mongo_database.user.update_one(
            {User.ID_: ObjectId(VALID_USER_ID)}, {"$unset": {field: 1}}
        )
