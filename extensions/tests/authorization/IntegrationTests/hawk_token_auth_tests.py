import json
import re
from datetime import datetime
from pathlib import Path

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    get_request_header_hawk,
)

from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.utils.token.hawk.exceptions import ErrorCodes

VALID_USER1_ID = "5e8f0c74b50aa9656c34789b"
VALID_USER2_ID = "601919b5c03550c421c075eb"
VALID_SUPER_ADMIN_ID = "602ce48712b129679a501570"
NAME = "name"
PRIMITIVE = "primitive"
VALUE = "value"
EXPECTED_RESULT_VALUE = "expectedResultValue"


class HawkTokenAuthTests(ExtensionTestCase):

    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
    ]

    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]

    def generate_auth_token(self) -> tuple[str, str]:
        rsp = self.flask_client.post(
            f"/api/auth/v1beta/user/{VALID_USER1_ID}/token",
            headers=self.headers_valid_user1,
        )
        return rsp.json["authKey"], rsp.json["authId"]

    def setUp(self):
        super(HawkTokenAuthTests, self).setUp()
        self.headers_super_admin = self.get_headers_for_token(VALID_SUPER_ADMIN_ID)
        self.headers_valid_user1 = self.get_headers_for_token(VALID_USER1_ID)
        self.headers_valid_user2 = self.get_headers_for_token(VALID_USER2_ID)
        self.base_url = "/api/extensions/v1beta/user"

    def test_success_generate_auth_token_for_user_and_login(self):
        rsp = self.flask_client.post(
            f"/api/auth/v1beta/user/{VALID_USER1_ID}/token",
            headers=self.headers_super_admin,
        )
        self.assertEqual(rsp.status_code, 201)
        self.assertIn("authKey", rsp.json)
        self.assertIn("authId", rsp.json)

        token = rsp.json["authKey"]
        user_key = rsp.json["authId"]

        url = f"{self.base_url}/{VALID_USER1_ID}"
        request_header = get_request_header_hawk(
            user_key=user_key,
            auth_key=token,
            url=f"http://localhost{url}",
            content=b"",
            content_type="",
            method="GET",
        )
        rsp = self.flask_client.get(
            url,
            headers={"Authorization": request_header},
        )
        self.assertEqual(rsp.json["id"], VALID_USER1_ID)

    def test_success_generate_auth_token_for_user_and_creation(self):
        rsp = self.flask_client.post(
            f"/api/auth/v1beta/user/{VALID_USER1_ID}/token",
            headers=self.headers_super_admin,
        )
        self.assertEqual(rsp.status_code, 201)
        self.assertIn("authKey", rsp.json)
        self.assertIn("authId", rsp.json)

        token = rsp.json["authKey"]
        user_key = rsp.json["authId"]

        url = f"/api/extensions/v1beta/user/profiles"

        data = {
            "limit": 20,
            "sort": {"fields": ["FLAGS"], "order": "DESCENDING"},
            "type": "[PatientsList] Load PatientsList",
        }
        byte_data = json.dumps(data).encode()
        request_header = get_request_header_hawk(
            user_key=user_key,
            auth_key=token,
            url=f"http://localhost{url}",
            content=byte_data,
            content_type="application/json",
            method="POST",
        )
        rsp = self.flask_client.post(
            url, headers={"Authorization": request_header}, json=data
        )
        self.assertNotEqual(rsp.status_code, 401)

    def test_failure_auth_token_login_wrong_id(self):
        private_key, user_key = self.generate_auth_token()
        url = f"{self.base_url}/{VALID_USER1_ID}"

        request_header = get_request_header_hawk(
            user_key=user_key,
            auth_key=private_key,
            url=f"http://localhost{url}",
            content=b"",
            content_type="",
            method="GET",
        )
        rsp = self.flask_client.get(
            url,
            headers={
                "Authorization": request_header.replace(
                    VALID_USER1_ID, "ffffffffffffffffffffffff"
                )
            },
        )

        self.assertEqual(rsp.status_code, 401)

    def test_failure_auth_token_login_wrong_mac(self):
        rgx = re.compile('mac="(.*?)"')
        private_key, user_key = self.generate_auth_token()
        url = f"{self.base_url}/{VALID_USER1_ID}"

        request_header = get_request_header_hawk(
            user_key=user_key,
            auth_key=private_key,
            url=f"http://localhost{url}",
            content=b"",
            content_type="",
            method="GET",
        )
        mac = rgx.search(request_header).group(1)

        rsp = self.flask_client.get(
            url,
            headers={"Authorization": request_header.replace(mac, "YQ==")},
        )

        self.assertEqual(rsp.status_code, 403)
        self.assertEqual(rsp.json["code"], ErrorCodes.HAWK_MAC_MISMATCH.value)

    def test_failure_security_generate_auth_token_for_other_user(self):
        rsp = self.flask_client.post(
            f"/api/auth/v1beta/user/{VALID_USER2_ID}/token",
            headers=self.headers_valid_user1,
        )

        self.assertEqual(rsp.status_code, 403)

    def test_success_security_generate_auth_token_as_super_admin(self):
        rsp = self.flask_client.post(
            f"/api/auth/v1beta/user/{VALID_USER1_ID}/token",
            headers=self.headers_super_admin,
        )

        self.assertEqual(rsp.status_code, 201)

    def test_success_nonce_validation_is_checked(self):
        private_key, user_key = self.generate_auth_token()
        url = f"{self.base_url}/{VALID_USER1_ID}"

        request_header = get_request_header_hawk(
            user_key=user_key,
            auth_key=private_key,
            url=f"http://localhost{url}",
            content=b"",
            content_type="",
            method="GET",
        )
        rsp = self.flask_client.get(
            url,
            headers={"Authorization": request_header},
        )
        self.assertEqual(rsp.status_code, 200)
        rsp = self.flask_client.get(
            url,
            headers={"Authorization": request_header},
        )
        self.assertEqual(rsp.status_code, 403)
        self.assertEqual(
            rsp.json["code"], ErrorCodes.HAWK_REQUEST_ALREADY_PROCESSED.value
        )

    def test_failure_unparsable_hawk_header(self):
        private_key, user_key = self.generate_auth_token()
        url = f"{self.base_url}/{VALID_USER1_ID}"

        request_header = get_request_header_hawk(
            user_key=user_key,
            auth_key=private_key,
            url=f"http://localhost{url}",
            content=b"",
            content_type="",
            method="GET",
        )
        # https://sentry.io/organizations/huma-therapeutics-ltd-qc/issues/2927209817/?project=5738131&referrer=jira_integration%5D
        request_header += (
            """, ext="hash="ijehcnSJT+mtpZvRbpv1FCCcfJhOMEtDn65eL06Msi8="" """
        )
        rsp = self.flask_client.get(
            url,
            headers={"Authorization": request_header},
        )
        self.assertEqual(400, rsp.status_code)

    def test_success_login_when_having_multiple_keys(self):
        self.generate_auth_token()
        private_key, user_key = self.generate_auth_token()
        url = f"{self.base_url}/{VALID_USER1_ID}"

        request_header = get_request_header_hawk(
            user_key=user_key,
            auth_key=private_key,
            url=f"http://localhost{url}",
            content=b"",
            content_type="",
            method="GET",
        )
        rsp = self.flask_client.get(
            url,
            headers={"Authorization": request_header},
        )
        self.assertEqual(rsp.status_code, 200)

    def test_failure_hawk_token_expiration(self):
        private_key, user_key = self.generate_auth_token()
        url = f"{self.base_url}/{VALID_USER1_ID}"

        request_header = get_request_header_hawk(
            user_key=user_key,
            auth_key=private_key,
            url=f"http://localhost{url}",
            content=b"",
            content_type="",
            method="GET",
        )
        with freeze_time(datetime.now() + relativedelta(hours=1)):
            rsp = self.flask_client.get(
                url,
                headers={"Authorization": request_header},
            )
            self.assertEqual(rsp.status_code, 403)
            self.assertEqual(rsp.json["code"], ErrorCodes.HAWK_TOKEN_EXPIRED.value)

    def test_failure_hawk_error_wrong_content_hash(self):
        private_key, user_key = self.generate_auth_token()
        url = f"{self.base_url}/{VALID_USER1_ID}"

        request_header = get_request_header_hawk(
            user_key=user_key,
            auth_key=private_key,
            url=f"http://localhost{url}",
            content=b"",
            content_type="wrong/content_type",
            method="GET",
        )

        rsp = self.flask_client.get(url, headers={"Authorization": request_header})
        self.assertEqual(rsp.status_code, 403)
        self.assertEqual(
            rsp.json["code"], ErrorCodes.HAWK_MIS_COMPUTED_CONTENT_HASH.value
        )

    def test_failure_hawk_malformed_user_key(self):
        url = f"{self.base_url}/{VALID_USER1_ID}"
        request_header = get_request_header_hawk(
            user_key="wronguserkey",
            auth_key="wrong_token",
            url=f"http://localhost{url}",
            content=b"",
            content_type="wrong/content_type",
            method="GET",
        )
        rsp = self.flask_client.get(url, headers={"Authorization": request_header})
        self.assertEqual(rsp.status_code, 403)
        self.assertEqual(rsp.json["code"], ErrorCodes.HAWK_INVALID_USER_KEY.value)

    def test_raise_error_gracefully_when_no_hawk_config(self):
        hawk_config = self.test_server.config.server.adapters.hawk
        self.test_server.config.server.adapters.hawk = None

        private_key, user_key = self.generate_auth_token()
        url = f"{self.base_url}/{VALID_USER1_ID}"

        request_header = get_request_header_hawk(
            user_key=user_key,
            auth_key=private_key,
            url=f"http://localhost{url}",
            content=b"",
            content_type="",
            method="GET",
        )

        rsp = self.flask_client.get(
            url,
            headers={"Authorization": request_header},
        )
        self.assertEqual(rsp.status_code, 403)

        self.test_server.config.server.adapters.hawk = hawk_config
