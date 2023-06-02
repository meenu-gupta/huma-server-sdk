import unittest

from sdk.auth.use_case.auth_use_cases import (
    RetrieveDeepLinkAndroidAppUseCase,
    RetrieveDeepLinkAppleAppUseCase,
)
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.di.components import read_config
from sdk.tests.application_test_utils.test_utils import SDK_CONFIG_PATH


class RetrieveDeeplinkTestCase(unittest.TestCase):
    EXPIRES_IN_MINUTES = 2880

    def setUp(self) -> None:
        self.phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)

    def test_retrieve_deeplink_ios(self):
        use_case = RetrieveDeepLinkAppleAppUseCase(self.phoenix_config)
        val = use_case.execute(None).value
        self.assertDictEqual(
            val,
            {
                "applinks": {
                    "apps": [],
                    "details": [
                        {"appIDs": ["TeamId.com.huma.iosappid"], "paths": ["*"]}
                    ],
                }
            },
        )

    def test_retrieve_deeplink_ios_config_not_exist(self):
        self.phoenix_config.server.project.clients[0].appIds = None
        use_case = RetrieveDeepLinkAppleAppUseCase(self.phoenix_config)
        with self.assertRaises(InvalidRequestException):
            _ = use_case.execute(None)

    def test_retrieve_deeplink_android(self):
        use_case = RetrieveDeepLinkAndroidAppUseCase(self.phoenix_config)
        val = use_case.execute(None)
        self.assertEqual(
            val,
            [
                {
                    "relation": ["delegate_permission/common.handle_all_urls"],
                    "target": {
                        "namespace": "android_app",
                        "package_name": "TeamId.com.huma.androidappid",
                        "sha256_cert_fingerprints": ["10:E1:03:22:12:25"],
                    },
                }
            ],
        )

    def test_retrieve_deeplink_android_config_not_exist(self):
        self.phoenix_config.server.project.clients[1].appIds = None
        use_case = RetrieveDeepLinkAndroidAppUseCase(self.phoenix_config)
        with self.assertRaises(InvalidRequestException):
            _ = use_case.execute(None)
