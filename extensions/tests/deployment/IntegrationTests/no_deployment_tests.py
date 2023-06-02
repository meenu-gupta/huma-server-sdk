from pathlib import Path

from extensions.authorization.component import AuthorizationComponent

from extensions.deployment.component import DeploymentComponent

from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.deployment.IntegrationTests.deployment_router_tests import (
    SearchDeploymentsTestCase,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent

from sdk.versioning.component import VersionComponent


VALID_USER_ID = "5e8f0c74b50aa9656c34789b"
DEPLOYMENT_COLLECTION = "deployment"


class NoDeploymentTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/no_deployment_dump.json")]
    override_config = {
        "server.deployment.enableAuthz": "true",
    }

    @classmethod
    def setUpClass(cls) -> None:
        super(NoDeploymentTestCase, cls).setUpClass()
        cls.deployment_route = "/api/extensions/v1beta"
        cls.section_id = "5e946c69e8002eac4a107f56"

    def setUp(self):
        super().setUp()
        self.headers = self.get_headers_for_token(VALID_USER_ID)

    def test_search_deployments(self):
        data = SearchDeploymentsTestCase.get_search_deployments_request_body()
        rsp = self.search(json=data)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, len(rsp.json["items"]))
        self.assertEqual(0, rsp.json["total"])

    def search(self, json):
        url = f"{self.deployment_route}/deployment/search"
        return self.flask_client.post(url, json=json, headers=self.headers)
