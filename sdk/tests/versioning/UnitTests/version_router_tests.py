import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.versioning.models.version import Version
from sdk.common.exceptions.exceptions import (
    PageNotFoundException,
    InvalidRequestException,
)
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.versioning.router.version_router import (
    retrieve_version,
    ping_pong,
    increase_version,
)

VERSION_ROUTER_PATH = "sdk.versioning.router.version_router"

testapp = Flask(__name__)
testapp.app_context().push()


class MockConfig:
    server = MagicMock()
    server.debugRouter = False


class VersionRouterTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._server_config = MagicMock()
        self._version = MagicMock()

        def bind(binder):
            binder.bind(PhoenixServerConfig, self._server_config)
            binder.bind(Version, self._version)

        inject.clear_and_configure(bind)

    @patch(f"{VERSION_ROUTER_PATH}.jsonify")
    def test_success_retrieve_version(self, jsonify):
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_version()
            jsonify.assert_called_with(self._version.to_dict())

    def test_success_ping_pong(self):
        with testapp.test_request_context("/", method="GET") as _:
            res = ping_pong()
            self.assertEqual(res[0], "pong")
            self.assertEqual(res[1], 200)

    def test_failure_increase_version_not_valid_version(self):
        self._server_config.server.debugRouter = True
        payload = {"serverVersion": "v34"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            with self.assertRaises(ConvertibleClassValidationError):
                increase_version()

    def test_failure_route_unaccessible(self):
        self._server_config.server.debugRouter = False
        payload = {"serverVersion": "v34"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            with self.assertRaises(PageNotFoundException):
                increase_version()

    def test_success_increase_version(self):
        self._server_config.server.debugRouter = True
        payload = {"serverVersion": "34.6.4"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            try:
                increase_version()
            except (InvalidRequestException, PageNotFoundException):
                self.fail()


if __name__ == "__main__":
    unittest.main()
