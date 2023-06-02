from packaging import version

from sdk.common.utils import inject
from sdk.tests.test_case import SdkTestCase
from sdk.versioning.component import VersionComponent
from sdk.versioning.models.version import Version, VersionField


class BaseVersioningTestCase(SdkTestCase):
    SERVER_VERSION = "1.3.1"
    API_VERSION = "v1"
    components = [
        VersionComponent(server_version=SERVER_VERSION, api_version=API_VERSION)
    ]

    @classmethod
    def setUpClass(cls) -> None:
        super(BaseVersioningTestCase, cls).setUpClass()
        cls.base_route = "/version"


class VersioningTestCase(BaseVersioningTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(VersioningTestCase, cls).setUpClass()
        cls.versions = inject.instance(Version)
        cls.ios_headers = {
            "x-hu-user-agent": "Huma-Dev/1.18.1 (bundleId: com.huma.HumaApp.dev; build: 76; software: iOS 14.2.0; hardware: iPhone; component: MedopadNetworking/1.0)"
        }

        cls.android_headers = {
            "x-hu-user-agent": "Huma-QA/1.18.0 (bundleId: com.huma.humaapp.qa; build:1; software: Android 29 (10); hardware: samsung SM-G970F)"
        }

        cls.web_headers = {
            "x-hu-user-agent": "Huma-Dev/1.18.1 (build: 111; software: Chrome 86.0.4240.193;)"
        }
        cls.headers = [cls.ios_headers, cls.android_headers, cls.web_headers]

    def setUp(self):
        super(VersioningTestCase, self).setUp()
        body = {
            "serverVersion": str(self.SERVER_VERSION),
            "apiVersion": self.API_VERSION,
        }
        self.flask_client.post(self.base_route, json=body)

    def test_success_ios_request_same_version(self):
        for header in self.headers:
            rsp = self.flask_client.get(self.base_route, headers=header)
            self.assertEqual(200, rsp.status_code)

    def test_success_request_greater_version(self):
        self.versions.server = VersionField("0.2.1")
        for header in self.headers:
            rsp = self.flask_client.get(self.base_route, headers=header)
            self.assertEqual(200, rsp.status_code)

    def test_success_request_lower_minor_version(self):
        self.versions.server = VersionField("1.4.1")
        for header in self.headers:
            rsp = self.flask_client.get(self.base_route, headers=header)
            self.assertEqual(200, rsp.status_code)

    def test_success_web_request_lower_version(self):
        self.versions.server = VersionField("2.2.1")
        rsp = self.flask_client.get(self.base_route, headers=self.web_headers)
        self.assertEqual(200, rsp.status_code)

    def test_failure_request_lower_version(self):
        self.versions.server = VersionField("2.2.1")
        for header in [self.ios_headers, self.android_headers]:
            rsp = self.flask_client.get(self.base_route, headers=header)
            self.assertEqual(426, rsp.status_code)

    def test_success_request_no_headers(self):
        rsp = self.flask_client.get(self.base_route)
        self.assertEqual(200, rsp.status_code)

    def test_success_update_version(self):
        body = {"serverVersion": "1.4.5", "apiVersion": "1.4.5"}
        rsp = self.flask_client.post(self.base_route, json=body)
        self.assertEqual(rsp.status_code, 200)

    def test_failure_update_version_wrong_version(self):
        body = {"serverVersion": "1.s.d", "apiVersion": "1.dda.5"}
        rsp = self.flask_client.post(self.base_route, json=body)
        self.assertEqual(rsp.status_code, 403)

    def test_failure_with_lower_than_minimum_version(self):
        ios_headers = {
            "x-hu-user-agent": "Huma-Dev/1.4.1 (bundleId: com.huma.HumaApp.dev; build: 76; software: iOS 14.2.0; hardware: iPhone; component: MedopadNetworking/1.0)"
        }

        android_headers = {
            "x-hu-user-agent": "Huma-QA/1.16.0 (bundleId: com.huma.humaapp.qa; build:1; software: Android 29 (10); hardware: samsung SM-G970F)"
        }
        for header in [ios_headers, android_headers]:
            rsp = self.flask_client.get(self.base_route, headers=header)
            self.assertEqual(426, rsp.status_code)

    def test_success_server_version_check_major_version(self):
        self.versions.server = VersionField("1.19.1")
        for header in [self.ios_headers, self.android_headers]:
            rsp = self.flask_client.get(self.base_route, headers=header)
            self.assertEqual(200, rsp.status_code)


class ServerDebugFalseVersioningTestCase(BaseVersioningTestCase):
    override_config = {"server.debugRouter": "false"}

    def test_success_version_retrieve(self):
        rsp = self.flask_client.get(self.base_route)
        self.assertEqual(rsp.status_code, 200)

    def test_version_update_not_found(self):
        body = {"serverVersion": "1.4.5", "apiVersion": "1.4.5"}
        rsp = self.flask_client.post(self.base_route, json=body)
        self.assertEqual(rsp.status_code, 404)
