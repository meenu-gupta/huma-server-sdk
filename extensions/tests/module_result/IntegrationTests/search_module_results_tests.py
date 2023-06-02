from pathlib import Path

from extensions.authorization.component import AuthorizationComponent
from extensions.common.sort import SortField
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.models.primitives import Questionnaire
from extensions.module_result.router.module_result_requests import (
    SearchModuleResultsRequestObject,
    BaseRetrieveModuleResultRequestObject,
)
from extensions.organization.component import OrganizationComponent
from extensions.tests.module_result.IntegrationTests.module_result_tests import now_str
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_surgery_details,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.versioning.component import VersionComponent

VALID_MANAGER_ID = "5e8f0c74b50aa9656c34789b"
VALID_USER_ID = "5e8f0c74b50aa9656c34789c"
VALID_ACCESS_CONTROLLER_ID = "602cfea54dcf4dc1f31c992c"

VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
VALID_ORG_ID = "5d386cc6ff885918d96eda1a"


class SearchModuleResultsTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        VersionComponent("1.17.1", "1.0"),
    ]
    config_file_path = Path(__file__).with_name("config.test.yaml")
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/module_results_dump.json"),
    ]

    def setUp(self):
        super().setUp()

        self.headers = self.get_headers_for_token(VALID_MANAGER_ID)
        self.base_route = (
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/search"
        )

    def test_search_weight_and_height(self):
        body = {
            "fromDateTime": "2020-01-01T10:00:00Z",
            "toDateTime": now_str(),
            "modules": ["Weight", "Height"],
        }

        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)

        response = rsp.json
        self.assertIn("Height", response)
        self.assertIn("Weight", response)

        self.assertEqual(8, len(response["Weight"]))
        self.assertEqual(3, len(response["Height"]))

    def test_success_search_with_access_controller(self):
        body = {
            SearchModuleResultsRequestObject.FROM_DATE_TIME: "2020-01-01T10:00:00Z",
            SearchModuleResultsRequestObject.TO_DATE_TIME: now_str(),
            SearchModuleResultsRequestObject.MODULES: ["Weight", "Height"],
        }
        headers = {
            "x-deployment-id": VALID_DEPLOYMENT_ID,
            **self.get_headers_for_token(VALID_ACCESS_CONTROLLER_ID),
        }
        rsp = self.flask_client.post(self.base_route, json=body, headers=headers)
        self.assertEqual(200, rsp.status_code)

    def test_search_modules_skip(self):
        body = {
            "fromDateTime": "2020-01-01T10:00:00Z",
            "toDateTime": now_str(),
            "skip": 1,
            "modules": ["Weight", "Height"],
        }

        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)

        response = rsp.json
        self.assertIn("Height", response)
        self.assertIn("Weight", response)

        self.assertEqual(7, len(response["Weight"]))
        self.assertEqual(2, len(response["Height"]))

    def test_search_modules_limit(self):
        body = {
            "fromDateTime": "2020-01-01T10:00:00Z",
            "toDateTime": now_str(),
            "limit": 2,
            "modules": ["Weight", "Height"],
        }

        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)

        response = rsp.json
        self.assertIn("Height", response)
        self.assertIn("Weight", response)

        self.assertEqual(2, len(response["Weight"]))
        self.assertEqual(2, len(response["Height"]))

    def test_search_surgery_details_returns_only_latest_record(self):
        module_id = "SurgeryDetails"
        submit_url = (
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/{module_id}"
        )
        search_url = f"{submit_url}/search"

        first_body = [sample_surgery_details()]
        rsp = self.flask_client.post(submit_url, json=first_body, headers=self.headers)
        self.assertEqual(201, rsp.status_code)
        first_id = rsp.json["ids"][0]

        second_body = [sample_surgery_details()]
        rsp = self.flask_client.post(submit_url, json=second_body, headers=self.headers)
        self.assertEqual(201, rsp.status_code)
        second_id = rsp.json["ids"][0]

        self.assertNotEqual(first_id, second_id)

        data = {
            BaseRetrieveModuleResultRequestObject.DIRECTION: SortField.Direction.DESC.value
        }
        search_rsp = self.flask_client.post(search_url, json=data, headers=self.headers)
        self.assertEqual(200, search_rsp.status_code)
        self.assertEqual(
            second_id, search_rsp.json["Questionnaire"][0][Questionnaire.ID]
        )
