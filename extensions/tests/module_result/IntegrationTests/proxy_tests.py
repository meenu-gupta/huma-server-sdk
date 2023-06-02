from pathlib import Path

from extensions.module_result.models.primitives import (
    Primitive,
    Questionnaire,
)
from extensions.tests.module_result.IntegrationTests.module_result_tests import (
    BaseModuleResultTest,
)
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_questionnaire,
)

VALID_PROXY_ID = "5e8f0c74b50aa9656c342220"
PROXY_PARTICIPANT_ID = "5e8f0c74b50aa9656c342222"
NOT_PROXY_PARTICIPANT_ID = "5e8f0c74b50aa9656c341111"


class ProxyIntegrationTests(BaseModuleResultTest):
    override_config = {"server.moduleResult.enableAuthz": "true"}
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/module_results_dump.json"),
    ]

    def test_success_submit_participants_results_as_proxy(self):
        headers = self.get_headers_for_token(VALID_PROXY_ID)
        data = sample_questionnaire()
        data[Questionnaire.QUESTIONNAIRE_ID] = "749e6294-034e-4366-a9c9-83027d5c0999"
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{PROXY_PARTICIPANT_ID}/module-result/Questionnaire",
            json=[data],
            headers=headers,
        )
        self.assertEqual(201, rsp.status_code)
        result_id = rsp.json["ids"][0]
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{PROXY_PARTICIPANT_ID}/primitive/Questionnaire/{result_id}",
            headers=headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(PROXY_PARTICIPANT_ID, rsp.json[Primitive.USER_ID])
        self.assertEqual(VALID_PROXY_ID, rsp.json[Primitive.SUBMITTER_ID])

    def test_failure_submit_results_as_proxy_for_not_connected_users(self):
        headers = self.get_headers_for_token(VALID_PROXY_ID)
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{NOT_PROXY_PARTICIPANT_ID}/module-result/Questionnaire",
            json=[sample_questionnaire()],
            headers=headers,
        )
        self.assertEqual(403, rsp.status_code)
        result_id = "5f50ffbeaad3c395ab806b88"
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{NOT_PROXY_PARTICIPANT_ID}/primitive/Weight/{result_id}",
            headers=headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_submit_results_as_proxy_for_another_participants_deployment(self):
        headers = self.get_headers_for_token(VALID_PROXY_ID)
        sample = sample_questionnaire()
        another_participants_deployment = "5d386cc6ff885918d96edb4a"
        sample[Primitive.DEPLOYMENT_ID] = another_participants_deployment
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{PROXY_PARTICIPANT_ID}/module-result/Questionnaire",
            json=[sample],
            headers=headers,
        )
        self.assertEqual(403, rsp.status_code)
        result_id = "5f50ffbeaad3c395ab806b89"
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{PROXY_PARTICIPANT_ID}/primitive/Weight/{result_id}",
            headers=headers,
        )
        self.assertEqual(403, rsp.status_code)
