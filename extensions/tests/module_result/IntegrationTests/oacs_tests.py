from extensions.module_result.exceptions import ModuleResultErrorCodes
from extensions.module_result.models.primitives import Questionnaire, OACS
from extensions.module_result.modules import OACSModule
from extensions.tests.module_result.IntegrationTests.module_result_tests import (
    BaseModuleResultTest,
)
from extensions.tests.module_result.IntegrationTests.test_samples import sample_oacs


class OACSModuleTest(BaseModuleResultTest):
    def test_success_create_module_result(self):
        data = sample_oacs()
        rsp = self.flask_client.post(
            f"{self.base_route}/{OACSModule.moduleId}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_failure_create_module_with_below_minimum_answers(self):
        data = sample_oacs(invalid=True)
        rsp = self.flask_client.post(
            f"{self.base_route}/{OACSModule.moduleId}",
            json=[data],
            headers=self.headers,
        )
        rsp_data = rsp.json
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(
            ModuleResultErrorCodes.NOT_ALL_QUESTIONS_ANSWERED, rsp_data["code"]
        )

    def test_success_retrieve(self):
        self.test_success_create_module_result()
        module_id = OACSModule.moduleId

        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search",
            json={"limit": 0, "skip": 0, "excludedFields": []},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        data = rsp.json
        self.assertIn(Questionnaire.__name__, data)
        self.assertIn(OACS.__name__, data)
