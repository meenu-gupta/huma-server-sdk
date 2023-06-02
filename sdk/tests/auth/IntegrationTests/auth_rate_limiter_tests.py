from pathlib import Path
from unittest.mock import patch

from sdk.auth.component import AuthComponent
from sdk.auth.enums import Method
from sdk.auth.use_case.auth_request_objects import (
    CheckAuthAttributesRequestObject,
    SignUpRequestObject,
    SendVerificationTokenRequestObject,
)
from sdk.common.adapter.email.mailgun_email_adapter import MailgunEmailAdapter
from sdk.common.adapter.twilio.twilio_sms_adapter import TwilioSmsAdapter
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.tests.application_test_utils.test_utils import IntegrationTestCase
from sdk.tests.auth.test_helpers import (
    USER_EMAIL,
    PROJECT_ID,
    CLIENT_ID_3,
    USER_PHONE_NUMBER,
)

TEST_RATE_LIMIT = 11


class AuthRateLimiterTestCase(IntegrationTestCase):
    config_file_path = Path(__file__).parent.parent.parent.joinpath(
        "application_test_utils/config.rate-limiter.test.yaml"
    )
    override_config = {
        "server.auth.rateLimit.signup": f"{TEST_RATE_LIMIT}/minute",
        "server.auth.rateLimit.checkAuthAttributes": f"{TEST_RATE_LIMIT}/minute",
        "server.adapters.oneTimePasswordRepo.rateLimit": TEST_RATE_LIMIT,
    }
    components = [AuthComponent()]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/auth_users_dump.json"),
    ]

    def setUp(self):
        super().setUp()
        self.test_server.rate_limiter.reset()

    def test_check_auth_attributes_rate_limiter(self):
        for request_number in range(TEST_RATE_LIMIT + 1):
            data = {
                CheckAuthAttributesRequestObject.EMAIL: USER_EMAIL,
                CheckAuthAttributesRequestObject.CLIENT_ID: CLIENT_ID_3,
                CheckAuthAttributesRequestObject.PROJECT_ID: PROJECT_ID,
            }
            response = self.flask_client.post(
                "/api/auth/v1beta/check-auth-attributes", json=data
            )
            if request_number != TEST_RATE_LIMIT:
                self.assertEqual(200, response.status_code)
            else:
                self.assertEqual(429, response.status_code)

    def test_signup_rate_limiter(self):
        for request_number in range(TEST_RATE_LIMIT + 1):
            data = {
                SignUpRequestObject.METHOD: Method.EMAIL,
                SignUpRequestObject.PHONE_NUMBER: USER_EMAIL,
            }
            response = self.flask_client.post("/api/auth/v1beta/signup", json=data)
            if request_number != TEST_RATE_LIMIT:
                # validation error will be raised
                self.assertEqual(403, response.status_code)
            else:
                self.assertEqual(429, response.status_code)

    def test_send_confirmation_code_email_rate_limiter(self):
        for request_number in range(TEST_RATE_LIMIT + 1):
            data = {
                SendVerificationTokenRequestObject.METHOD: 0,
                SendVerificationTokenRequestObject.EMAIL: USER_EMAIL,
                SendVerificationTokenRequestObject.CLIENT_ID: CLIENT_ID_3,
                SendVerificationTokenRequestObject.PROJECT_ID: PROJECT_ID,
            }
            with patch.object(MailgunEmailAdapter, "send_html_email"):
                response = self.flask_client.post(
                    "/api/auth/v1beta/sendverificationtoken", json=data
                )
            if request_number != TEST_RATE_LIMIT:
                self.assertEqual(200, response.status_code)
            else:
                self.assertEqual(429, response.status_code)
                self.assertEqual(ErrorCodes.RATE_LIMIT_EXCEEDED, response.json["code"])

    def test_send_confirmation_code_sms_rate_limiter(self):
        for request_number in range(TEST_RATE_LIMIT + 1):
            data = {
                SendVerificationTokenRequestObject.METHOD: 1,
                SendVerificationTokenRequestObject.PHONE_NUMBER: USER_PHONE_NUMBER,
                SendVerificationTokenRequestObject.CLIENT_ID: CLIENT_ID_3,
                SendVerificationTokenRequestObject.PROJECT_ID: PROJECT_ID,
            }
            with patch.object(TwilioSmsAdapter, "send_sms"):
                response = self.flask_client.post(
                    "/api/auth/v1beta/sendverificationtoken", json=data
                )
            if request_number != TEST_RATE_LIMIT:
                self.assertEqual(200, response.status_code)
            else:
                self.assertEqual(429, response.status_code)
                self.assertEqual(ErrorCodes.RATE_LIMIT_EXCEEDED, response.json["code"])
