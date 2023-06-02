from extensions.deployment.component import DeploymentComponent
from extensions.deployment.router.deployment_public_router import Region
from extensions.tests.test_case import ExtensionTestCase
from sdk.phoenix.config.server_config import Client

PROJECT_ID = "project_id"
MINIMUM_VERSION = "1.17.1"
VALID_CLIENT_ID_1 = "c1"
DEFAULT_BUCKET = "defaultBucket"


class RegionAPITestCase(ExtensionTestCase):
    components = [DeploymentComponent()]
    override_config = {
        "server.project.id": PROJECT_ID,
        "server.project.clients": [
            {
                Client.NAME: "USER_IOS - client",
                Client.CLIENT_ID: VALID_CLIENT_ID_1,
                Client.CLIENT_TYPE: "USER_IOS",
                Client.ROLE_IDS: ["User", "Manager", "SuperAdmin", "Proxy"],
                Client.MINIMUM_VERSION: MINIMUM_VERSION,
            }
        ],
        "server.storage.defaultBucket": DEFAULT_BUCKET,
    }

    @classmethod
    def setUpClass(cls) -> None:
        super(RegionAPITestCase, cls).setUpClass()
        cls.route = "/api/public/v1beta/region"

    def test_success_get_region_info_with_valid_client_id(self):
        get_rsp = self.flask_client.get(f"{self.route}?clientId={VALID_CLIENT_ID_1}")
        self.assertEqual(200, get_rsp.status_code)
        self.assertDictEqual(
            get_rsp.json,
            {
                Region.BUCKET: DEFAULT_BUCKET,
                Region.BUCKET_REGION: "us-west-2",
                Region.CLIENT_ID: VALID_CLIENT_ID_1,
                Region.COUNTRY_CODE: "gb",
                Region.END_POINT_URL: "https://localhost/",
                Region.MINIMUM_VERSION: MINIMUM_VERSION,
                Region.PROJECT_ID: PROJECT_ID,
                Region.STAGE: "DYNAMIC",
            },
        )

    def test_failure_get_region_info_with_invalid_client_id(self):
        client_id = "invalid id"
        get_rsp = self.flask_client.get(f"{self.route}?clientId={client_id}")
        self.assertEqual(400, get_rsp.status_code)
        self.assertEqual(100002, get_rsp.json["code"])
