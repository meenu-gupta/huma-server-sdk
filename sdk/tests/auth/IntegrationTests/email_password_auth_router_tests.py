from pathlib import Path
from unittest.mock import patch

import jwt
from bson import ObjectId

from sdk.auth.component import AuthComponent
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.use_case.auth_request_objects import (
    ConfirmationRequestObject,
    ResetPasswordRequestObject,
    RequestPasswordResetRequestObject,
    SendVerificationTokenRequestObject,
    SendVerificationTokenMethod,
)
from sdk.common.adapter.email_confirmation_adapter import EmailConfirmationAdapter
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import Client
from sdk.tests.auth.mock_objects import (
    SIGNUP_GIVEN_NAME,
    CURRENT_PASSWORD,
)
from .auth_router_tests import BaseSignUpTestCase

X_HU_LOCALE = "x-hu-locale"
MOCKED_PASSWORD = "$2b$12$hsS8Gi113IXUxe2Cw2Yc4.mFNcGaFeZJSWjP2IKAIxeFQwkYngDsu"
SAMPLE_PASSWORD = "Aa321123"
RESET_CODE_TYPE = EmailConfirmationAdapter.RESET_PASSWORD_CODE_TYPE


class EmailPasswordAuthTestCase(BaseSignUpTestCase):
    EXISTING_USER_EMAIL = "user@test.com"
    components = [AuthComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]

    def setUp(self):
        super(EmailPasswordAuthTestCase, self).setUp()
        self.user_id = self._sign_up_user(
            email=self.EXISTING_USER_EMAIL,
            userAttributes={"givenName": SIGNUP_GIVEN_NAME},
        )

    def test_send_email_confirmation_code_called(self):
        data = {
            SendVerificationTokenRequestObject.EMAIL: self.EXISTING_USER_EMAIL,
            SendVerificationTokenRequestObject.CLIENT_ID: "ctest1",
            SendVerificationTokenRequestObject.PROJECT_ID: "ptest1",
            SendVerificationTokenRequestObject.METHOD: 2,
        }
        rsp = self.flask_client.post(
            "/api/auth/v1beta/sendverificationtoken", json=data
        )
        self.assertEqual(200, rsp.status_code)

        call_args = {
            "to": self.EXISTING_USER_EMAIL,
            "locale": Language.EN,
            "client": Client.from_dict(
                {
                    Client.NAME: "USER_IOS-client",
                    Client.CLIENT_ID: "ctest1",
                    Client.CLIENT_TYPE: "USER_IOS",
                    Client.APP_IDS: ["TeamId.com.huma.iosappid"],
                    Client.DEEP_LINK_BASE_URL: "http://url.com",
                    Client.MINIMUM_VERSION: "1.17.1",
                }
            ),
            "username": SIGNUP_GIVEN_NAME,
            "method": SendVerificationTokenMethod.EMAIL_SIGNUP_CONFIRMATION,
        }
        self.confirmation_adapter.send_confirmation_email.assert_called_once_with(
            **call_args
        )

    def test_send_email_verification_code_called(self):
        data = {
            SendVerificationTokenRequestObject.EMAIL: self.EXISTING_USER_EMAIL,
            SendVerificationTokenRequestObject.CLIENT_ID: "ctest1",
            SendVerificationTokenRequestObject.PROJECT_ID: "ptest1",
            SendVerificationTokenRequestObject.METHOD: 0,
        }
        rsp = self.flask_client.post(
            "/api/auth/v1beta/sendverificationtoken", json=data
        )
        self.assertEqual(200, rsp.status_code)

        call_args = {
            "to": self.EXISTING_USER_EMAIL,
            "locale": Language.EN,
            "client": Client.from_dict(
                {
                    Client.NAME: "USER_IOS-client",
                    Client.CLIENT_ID: "ctest1",
                    Client.CLIENT_TYPE: "USER_IOS",
                    Client.APP_IDS: ["TeamId.com.huma.iosappid"],
                    Client.DEEP_LINK_BASE_URL: "http://url.com",
                    Client.MINIMUM_VERSION: "1.17.1",
                }
            ),
            "username": SIGNUP_GIVEN_NAME,
        }
        self.verification_adapter.send_verification_email.assert_called_once_with(
            **call_args
        )

    def test_confirm_email_valid_simple_code(self):
        self.confirmation_adapter.code = "12345678"
        data = {
            ConfirmationRequestObject.EMAIL: self.EXISTING_USER_EMAIL,
            ConfirmationRequestObject.CONFIRMATION_CODE: "12345678",
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
        }
        rsp = self.flask_client.post("/api/auth/v1beta/confirm", json=data)
        self.assertEqual(200, rsp.status_code)

    def test_failure_confirm_email_no_data_in_body(self):
        rsp = self.flask_client.post("/api/auth/v1beta/confirm")
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(rsp.json["code"], ErrorCodes.INVALID_REQUEST)

    def test_confirm_email_valid_jwt_token(self):
        code = jwt.encode({}, "test").decode("utf-8")
        self.confirmation_adapter.code = code
        data = {
            ConfirmationRequestObject.EMAIL: self.EXISTING_USER_EMAIL,
            ConfirmationRequestObject.CONFIRMATION_CODE: code,
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
        }
        rsp = self.flask_client.post("/api/auth/v1beta/confirm", json=data)
        self.assertEqual(200, rsp.status_code)


class ResetPasswordTestCase(BaseSignUpTestCase):
    EXISTING_USER_EMAIL = "user@test.com"

    def setUp(self):
        super().setUp()
        self.user_id = self._sign_up_user(email=self.EXISTING_USER_EMAIL)

    def test_request_password_reset(self):
        data = {
            RequestPasswordResetRequestObject.EMAIL: self.EXISTING_USER_EMAIL,
            RequestPasswordResetRequestObject.CLIENT_ID: "ctest1",
            RequestPasswordResetRequestObject.PROJECT_ID: "ptest1",
        }
        rsp = self.flask_client.post(
            "/api/auth/v1beta/request-password-reset", json=data
        )
        self.assertEqual(200, rsp.status_code)
        self.confirmation_adapter.send_reset_password_email.assert_called_once()
        self.confirmation_adapter.send_reset_password_email.reset_mock()

        rsp = self.flask_client.post(
            "/api/auth/v1beta/request-password-reset", json=data
        )
        self.assertEqual(200, rsp.status_code)
        self.confirmation_adapter.send_reset_password_email.assert_called_once()

    @patch("sdk.auth.use_case.auth_use_cases.hash_new_password")
    def test_reset_password_request_email(self, hash_pass_mock):
        hash_pass_mock.return_value = MOCKED_PASSWORD
        data = {
            RequestPasswordResetRequestObject.EMAIL: self.EXISTING_USER_EMAIL,
            RequestPasswordResetRequestObject.CLIENT_ID: "ctest1",
            RequestPasswordResetRequestObject.PROJECT_ID: "ptest1",
        }
        rsp = self.flask_client.post(
            "/api/auth/v1beta/request-password-reset",
            json=data,
            headers={X_HU_LOCALE: Language.FR},
        )
        self.assertEqual(200, rsp.status_code)
        adapter = self.confirmation_adapter
        lang = adapter.send_reset_password_email.call_args.kwargs["locale"]
        self.assertEqual(Language.FR, lang)
        adapter.send_reset_password_email.reset_mock()

        rsp = self.flask_client.post(
            "/api/auth/v1beta/request-password-reset", json=data
        )
        self.assertEqual(200, rsp.status_code)
        lang = adapter.send_reset_password_email.call_args.kwargs["locale"]
        self.assertEqual(Language.EN, lang)

    @patch("sdk.auth.helpers.auth_helpers.hash_new_password")
    def test_password_reset_valid(self, mocked_hash_password):
        hashed_password = "$2b$12$JoyWB6XiHG4KC6ZWyy6JcZ38x06lKQX9OpxySn/plLLtsudAJcO"
        mocked_hash_password.return_value = hashed_password
        code = self.confirmation_adapter.create_or_retrieve_code_for(
            self.EXISTING_USER_EMAIL, RESET_CODE_TYPE
        )
        data = {
            ResetPasswordRequestObject.EMAIL: self.EXISTING_USER_EMAIL,
            ResetPasswordRequestObject.NEW_PASSWORD: SAMPLE_PASSWORD,
            ResetPasswordRequestObject.CODE: code,
        }
        rsp = self.flask_client.post("/api/auth/v1beta/password-reset", json=data)
        self.assertEqual(200, rsp.status_code)

        # test that password update datetime changed
        user = self.mongo_database["authuser"].find_one(
            {AuthUser.ID_: ObjectId(self.user_id)}
        )
        password_update_datetime = user.get(AuthUser.PASSWORD_UPDATE_DATE_TIME)
        self.assertIsNotNone(password_update_datetime)

    def test_reset_password__code_valid_after_recent_pass_exception(self):
        self.mongo_database.authuser.update_one(
            {"_id": ObjectId(self.user_id)},
            {
                "$set": {
                    "hashedPassword": "$2b$12$ETJvHcEGajnF7DekRGo7p./HQYnmlAICUe2HRkuKjc8Ti4FOFXh6m"
                }
            },
        )
        code = self.confirmation_adapter.create_or_retrieve_code_for(
            self.EXISTING_USER_EMAIL, RESET_CODE_TYPE
        )
        data = {
            ResetPasswordRequestObject.EMAIL: self.EXISTING_USER_EMAIL,
            ResetPasswordRequestObject.NEW_PASSWORD: CURRENT_PASSWORD,
            ResetPasswordRequestObject.CODE: code,
        }
        rsp = self.flask_client.post("/api/auth/v1beta/password-reset", json=data)
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(ErrorCodes.ALREADY_USED_PASSWORD, rsp.json["code"])

        rsp = self.flask_client.post("/api/auth/v1beta/password-reset", json=data)
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(ErrorCodes.ALREADY_USED_PASSWORD, rsp.json["code"])


class ResetPasswordRealAdapterTestCase(BaseSignUpTestCase):
    EXISTING_USER_EMAIL = "user@test.com"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        inject.get_injector().rebind(
            lambda b: b.bind(EmailConfirmationAdapter, EmailConfirmationAdapter())
        )

    def setUp(self):
        super().setUp()
        self._sign_up_user(email=self.EXISTING_USER_EMAIL)

    @patch("sdk.auth.helpers.auth_helpers.hash_new_password")
    def test_reset_password__code_not_valid_after_first_use(self, mocked_hash_password):
        mocked_hash_password.return_value = MOCKED_PASSWORD
        code = self.confirmation_adapter.create_or_retrieve_code_for(
            self.EXISTING_USER_EMAIL, RESET_CODE_TYPE
        )
        data = {
            ResetPasswordRequestObject.EMAIL: self.EXISTING_USER_EMAIL,
            ResetPasswordRequestObject.NEW_PASSWORD: SAMPLE_PASSWORD,
            ResetPasswordRequestObject.CODE: code,
        }
        rsp = self.flask_client.post("/api/auth/v1beta/password-reset", json=data)
        self.assertEqual(200, rsp.status_code)

        rsp = self.flask_client.post("/api/auth/v1beta/password-reset", json=data)
        self.assertEqual(401, rsp.status_code)
        self.assertEqual(ErrorCodes.INVALID_EMAIL_CONFIRMATION_CODE, rsp.json["code"])
