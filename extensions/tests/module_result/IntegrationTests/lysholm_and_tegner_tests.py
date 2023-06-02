from extensions.module_result.models.primitives import Questionnaire, Lysholm, Tegner
from extensions.module_result.modules import LysholmTegnerModule
from extensions.tests.module_result.IntegrationTests.module_result_tests import (
    BaseModuleResultTest,
)
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_lysholm_and_tegner,
)


class LysholmAndTegnerModuleTest(BaseModuleResultTest):
    def test_success_create_module_result(self):
        data = sample_lysholm_and_tegner()
        rsp = self.flask_client.post(
            f"{self.base_route}/{LysholmTegnerModule.moduleId}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_success_retrieve(self):
        self.test_success_create_module_result()
        module_id = LysholmTegnerModule.moduleId

        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        data = rsp.json
        self.assertIn(Questionnaire.__name__, data)
        self.assertIn(Lysholm.__name__, data)
        self.assertIn(Tegner.__name__, data)
        self.assertEqual(97, data[Lysholm.__name__][0][Lysholm.LYSHOLM])
