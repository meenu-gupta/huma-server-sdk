import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.deployment.router.deployment_public_router import (
    check_activation_code,
    get_region,
    Region,
)
from extensions.tests.shared.test_helpers import get_server_project
from sdk.common.exceptions.exceptions import InvalidClientIdException
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.tests.auth.test_helpers import TEST_CLIENT_ID

DEPLOYMENT_PUBLIC_ROUTER_PATH = "extensions.deployment.router.deployment_public_router"

DEFAULT_BUCKET = "defaultBucket"

testapp = Flask(__name__)
testapp.app_context().push()

SAMPLE_PROJECT = get_server_project()
EXPECTED_RESULT = {
    Region.BUCKET: DEFAULT_BUCKET,
    Region.BUCKET_REGION: "us-west-2",
    Region.CLIENT_ID: TEST_CLIENT_ID,
    Region.COUNTRY_CODE: "gb",
    Region.END_POINT_URL: "https://localhost/",
    Region.PROJECT_ID: SAMPLE_PROJECT.id,
    Region.STAGE: "DYNAMIC",
}


class DeploymentPublicRouterTestCase(unittest.TestCase):
    @patch(f"{DEPLOYMENT_PUBLIC_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_PUBLIC_ROUTER_PATH}.DeploymentService")
    def test_success_check_activation_code(self, service, jsonify):
        code = 111111
        service().retrieve_deployment_with_code.return_value = MagicMock(), 2, 3
        with testapp.test_request_context("/", method="GET") as _:
            check_activation_code(code)
            service().retrieve_deployment_with_code.assert_called_with(code)


class RegionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._config = MagicMock()
        self._config.server.project = get_server_project()
        self._config.server.storage.defaultBucket = DEFAULT_BUCKET

        def bind_and_configure(binder):
            binder.bind(PhoenixServerConfig, self._config)

        inject.clear_and_configure(bind_and_configure)

    @patch(f"{DEPLOYMENT_PUBLIC_ROUTER_PATH}.jsonify")
    def test_success_region_with_valid_client_id(self, mock_jsonify):
        with testapp.test_request_context("/", method="GET") as req:
            req.request.args = {"clientId": TEST_CLIENT_ID}
            get_region()
            res = {
                **EXPECTED_RESULT,
                Region.MINIMUM_VERSION: str(SAMPLE_PROJECT.clients[0].minimumVersion),
            }
            mock_jsonify.assert_called_with(res)

    def test_failure_region_with_invalid_client_id(self):
        client_id = "invalid id"
        with testapp.test_request_context("/", method="GET") as req:
            req.request.args = {"clientId": client_id}
            with self.assertRaises(InvalidClientIdException):
                get_region()

    def test_failure_with_invalid_client_id(self):
        with self.assertRaises(InvalidClientIdException):
            Region.from_dict(
                {
                    Region.BUCKET: "bucket",
                    Region.CLIENT_ID: "invalid client id",
                    Region.PROJECT_ID: SAMPLE_PROJECT.id,
                    Region.END_POINT_URL: "https://google.com",
                }
            )

    def test_success_region_with_type_qr_code(self):
        with testapp.test_request_context("/", method="GET") as req:
            req.request.args = {"clientId": TEST_CLIENT_ID, "type": "qrCode"}
            res = get_region()
            self.assertEqual("image/png", res.mimetype)


if __name__ == "__main__":
    unittest.main()
