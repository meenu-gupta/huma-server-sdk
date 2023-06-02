from pathlib import Path

from sdk.auth.component import AuthComponent
from sdk.phoenix.config.server_config import Client
from sdk.tests.auth.test_helpers import PROJECT_ID
from sdk.tests.test_case import SdkTestCase


def get_override_config():
    return {
        "server.project.id": PROJECT_ID,
        "server.project.clients": [
            {
                Client.NAME: "MANAGER_WEB-client",
                Client.CLIENT_ID: "c3",
                Client.CLIENT_TYPE: "MANAGER_WEB",
                Client.AUTH_TYPE: "MFA",
            },
            {
                Client.NAME: "USER_IOS-client",
                Client.CLIENT_ID: "c2",
                Client.CLIENT_TYPE: "USER_IOS",
                Client.APP_IDS: ["TeamId.com.huma.iosappid"],
            },
            {
                Client.NAME: "USER_ANDROID-client",
                Client.CLIENT_ID: "ctest1",
                Client.CLIENT_TYPE: "USER_ANDROID",
                Client.APP_IDS: ["TeamId.com.huma.androidappid"],
                Client.FINGERPRINTS: ["10:E1:03:22:12:25"],
            },
        ],
    }


class RetrieveDeeplinkIosTestCase(SdkTestCase):
    components = [AuthComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/auth_users_dump.json")]
    override_config = get_override_config()

    def setUp(self):
        super(RetrieveDeeplinkIosTestCase, self).setUp()

    def test_retrieve_deeplink_ios_success(self):
        rsp = self.flask_client.get(".well-known/apple-app-site-association")
        self.assertEqual(rsp.status_code, 200)
        self.assertDictEqual(
            rsp.json,
            {
                "applinks": {
                    "apps": [],
                    "details": [
                        {"appIDs": ["TeamId.com.huma.iosappid"], "paths": ["*"]}
                    ],
                }
            },
        )


class RetrieveDeeplinkIosFailureTestCase(SdkTestCase):
    components = [AuthComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/auth_users_dump.json")]
    override_config = {
        "server.project.id": PROJECT_ID,
        "server.project.clients": [
            {
                Client.NAME: "USER_IOS-client",
                Client.CLIENT_ID: "c2",
                Client.CLIENT_TYPE: "USER_IOS",
            }
        ],
    }

    def setUp(self):
        super(RetrieveDeeplinkIosFailureTestCase, self).setUp()

    def test_retrieve_deeplink_ios_failure_with_no_config(self):
        rsp = self.flask_client.get(".well-known/apple-app-site-association")
        self.assertEqual(rsp.status_code, 400)


class RetrieveDeeplinkAndroidTestCase(SdkTestCase):
    components = [AuthComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/auth_users_dump.json")]
    override_config = get_override_config()

    def setUp(self):
        super(RetrieveDeeplinkAndroidTestCase, self).setUp()

    def test_retrieve_deeplink_android_success(self):
        rsp = self.flask_client.get(".well-known/assetlinks.json")
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(
            rsp.json,
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


class RetrieveDeeplinkAndroidFailureTestCase(SdkTestCase):
    components = [AuthComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/auth_users_dump.json")]
    override_config = {
        "server.project.id": PROJECT_ID,
        "server.project.clients": [
            {
                Client.NAME: "USER_ANDROID-client",
                Client.CLIENT_ID: "ctest1",
                Client.CLIENT_TYPE: "USER_ANDROID",
            }
        ],
    }

    def setUp(self):
        super(RetrieveDeeplinkAndroidFailureTestCase, self).setUp()

    def test_retrieve_deeplink_android_failure_with_no_config(self):
        rsp = self.flask_client.get(".well-known/assetlinks.json")
        self.assertEqual(rsp.status_code, 400)
