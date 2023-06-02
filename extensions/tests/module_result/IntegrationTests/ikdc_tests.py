from extensions.module_result.models.primitives import Questionnaire, IKDC
from extensions.module_result.modules import IKDCModule
from extensions.tests.module_result.IntegrationTests.module_result_tests import (
    BaseModuleResultTest,
)
from extensions.tests.module_result.IntegrationTests.test_samples import sample_ikdc
from sdk.common.exceptions.exceptions import ErrorCodes


class IKDCModuleTest(BaseModuleResultTest):
    def test_success_create_module_result(self):
        data = sample_ikdc()
        rsp = self.flask_client.post(
            f"{self.base_route}/{IKDCModule.moduleId}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_failure_create_module_with_invalid_scale_format_answers(self):
        data = sample_ikdc(invalid=True)
        rsp = self.flask_client.post(
            f"{self.base_route}/{IKDCModule.moduleId}",
            json=[data],
            headers=self.headers,
        )
        rsp_data = rsp.json
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp_data["code"])

    def test_success_retrieve(self):
        self.test_success_create_module_result()
        module_id = IKDCModule.moduleId

        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search",
            json={"limit": 0, "skip": 0, "excludedFields": []},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        data = rsp.json
        self.assertIn(Questionnaire.__name__, data)
        self.assertIn(IKDC.__name__, data)
