import unittest
from unittest.mock import MagicMock

from sdk.common.decorator.debug_route import debug_route
from sdk.common.exceptions.exceptions import PageNotFoundException
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig


class MockConfig:
    server = MagicMock()
    server.debugRouter = True


class DebugRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.server_config = MockConfig()

        def bind(binder):
            binder.bind(PhoenixServerConfig, self.server_config)

        inject.clear_and_configure(bind)

        @debug_route()
        def func():
            return "func"

        self.decorated_func = func

    def test_success_debug_route(self):
        self.server_config.server.debugRouter = True
        self.assertEqual(self.decorated_func(), "func")

    def test_failure_debug_route(self):
        self.server_config.server.debugRouter = False
        with self.assertRaises(PageNotFoundException):
            self.decorated_func()
