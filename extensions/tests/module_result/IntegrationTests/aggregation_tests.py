from pathlib import Path

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.versioning.component import VersionComponent

VALID_MANAGER_ID = "5e8f0c74b50aa9656c34789b"
VALID_USER_ID = "5e8f0c74b50aa9656c34789c"

VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"


class ModuleResultsAggregationTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    config_file_path = Path(__file__).with_name("config.test.yaml")
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/aggregation_dump.json"),
    ]

    def setUp(self):
        super().setUp()

        self.headers = self.get_headers_for_token(VALID_MANAGER_ID)
        self.submit_route = (
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/Weight"
        )
        self.aggregate_route = (
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/aggregate"
        )

    def test_aggregate_by_start_date(self):
        body = {
            "fromDateTime": "2020-09-03T13:37:50.775000Z",
            "toDateTime": "2020-09-04T14:37:50.775000Z",
            "mode": "MONTHLY",
            "function": "AVG",
            "primitiveName": "Weight",
        }

        # checking values in db for 2020-09-03T14:37:50.775000Z
        rsp = self.flask_client.post(
            self.aggregate_route, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(100.0, rsp.json[0]["value"])

        weight = {
            "type": "Weight",
            "deviceName": "iOS",
            "deploymentId": VALID_DEPLOYMENT_ID,
            "startDateTime": "2020-09-03T14:37:50.775000Z",
            "value": 130,
        }

        # create new values with same startDateTime(2020-09-03T14:37:50.775000Z)
        rsp = self.flask_client.post(
            self.submit_route, json=[weight], headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        # check if aggregation counts newly created value as old value
        rsp = self.flask_client.post(
            self.aggregate_route, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(110.0, rsp.json[0]["value"])
