import unittest
from datetime import datetime, timedelta
from pathlib import Path

import jwt
from bson import ObjectId
from freezegun import freeze_time
from werkzeug.test import TestResponse

from extensions.tests.utils import sample_user
from sdk.auth.component import AuthComponent
from sdk.auth.enums import AuthStage, Method
from sdk.auth.model.auth_user import AuthUser, AuthIdentifierType
from sdk.auth.model.session import DeviceSessionV1
from sdk.auth.repository.mongo_auth_repository import MongoAuthRepository
from sdk.auth.use_case.auth_request_objects import (
    SignUpRequestObject,
    SendVerificationTokenRequestObject,
    SendVerificationTokenMethod,
    ConfirmationRequestObject,
    SetAuthAttributesRequestObject,
    SignInRequestObject,
    CheckAuthAttributesRequestObject,
    SignOutRequestObject,
    SignInRequestObjectV1,
    SignOutRequestObjectV1,
    RefreshTokenRequestObjectV1,
)
from sdk.auth.use_case.auth_response_objects import RefreshTokenResponseObject
from sdk.auth.use_case.auth_use_cases import mask_phone_number
from sdk.common.adapter.email_confirmation_adapter import EmailConfirmationAdapter
from sdk.common.adapter.email_verification_adapter import EmailVerificationAdapter
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.common.utils.token.jwt.jwt import USER_CLAIMS_KEY, AUTH_STAGE
from sdk.common.utils.validators import remove_none_values
from sdk.tests.auth.mock_objects import (
    MockEmailAdapter,
    MockSmsAdapter,
    MockEmailConfirmationAdapter,
    sample_sign_up_data,
)
from sdk.tests.auth.test_helpers import (
    USER_PASSWORD,
    NOT_EXISTING_EMAIL,
    USER_EMAIL,
    USER_PHONE_NUMBER,
    PROJECT_ID,
    CLIENT_ID_3,
)
from sdk.tests.test_case import SdkTestCase

USER_COLLECTION = MongoAuthRepository.USER_COLLECTION
SESSION_COLLECTION = MongoAuthRepository.SESSION_COLLECTION


class BaseSignUpTestCase(SdkTestCase):
    components = [AuthComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]
    confirmation_adapter = None
    verification_adapter = None
    sms_adapter = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.confirmation_adapter = MockEmailConfirmationAdapter()
        cls.sms_adapter = MockSmsAdapter()
        cls.verification_adapter = MockEmailAdapter()

        def mock_adapters(binder: Binder):
            binder.bind(EmailVerificationAdapter, cls.verification_adapter)
            binder.bind(EmailConfirmationAdapter, cls.confirmation_adapter)
            binder.bind("aliCloudSmsVerificationAdapter", cls.sms_adapter)
            binder.bind("twilioSmsVerificationAdapter", cls.sms_adapter)

        inject.get_injector_or_die().rebind(mock_adapters)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        inject.clear()

    def tearDown(self):
        super().tearDown()
        self.confirmation_adapter.send_confirmation_email.reset_mock()
        self.confirmation_adapter.send_reset_password_email.reset_mock()
        self.verification_adapter.send_verification_email.reset_mock()

    def _sign_up_user(self, **kwargs):
        data = sample_user()
        if kwargs:
            data.update(kwargs)

        rsp = self.flask_client.post("/api/auth/v1beta/signup", json=data)
        self.assertEqual(200, rsp.status_code)
        return rsp.json["uid"]


class SignUpTestCase(BaseSignUpTestCase):
    def test_success_email_password_sign_up(self):
        rsp = self.flask_client.post(
            "/api/auth/v1beta/signup", json=sample_sign_up_data()
        )
        self.assertEqual(200, rsp.status_code)

    def test_failure_email_password_signup__password_missing(self):
        data = sample_sign_up_data()
        data.pop(SignUpRequestObject.PASSWORD)
        rsp = self.flask_client.post("/api/auth/v1beta/signup", json=data)
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_email_password_sign_up_same_email_different_case(self):
        email = "test_user@test.com"
        rsp = self.flask_client.post(
            "/api/auth/v1beta/signup", json=sample_sign_up_data(email)
        )
        self.assertEqual(200, rsp.status_code)
        rsp = self.flask_client.post(
            "/api/auth/v1beta/signup", json=sample_sign_up_data(email.upper())
        )
        self.assertEqual(400, rsp.status_code)

    def test_email_password_sign_up_existing_email_upper_case(self):
        existing_email = "userTEST2@test.com"

        rsp = self.flask_client.post(
            "/api/auth/v1beta/signup", json=sample_sign_up_data(existing_email.lower())
        )
        self.assertEqual(400, rsp.status_code)


class PhoneSignUpTestCase(BaseSignUpTestCase):
    def test_duplicated_username_and_password(self):
        self._sign_up_user()
        rsp = self.flask_client.post("/api/auth/v1beta/signup", json=sample_user())
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.json["code"], 100010)

    def test_two_users_in_two_deployment(self):
        self._sign_up_user()
        another_user = sample_user()
        another_user["phoneNumber"] = "+447484889825"
        another_user["email"] = "m@medopad.com"
        another_user["validationData"]["activationCode"] = "05677151"
        rsp = self.flask_client.post("/api/auth/v1beta/signup", json=another_user)
        self.assertEqual(rsp.status_code, 200)


class SendPhoneVerificationTokenTestCase(BaseSignUpTestCase):
    def test_send_verification(self):
        self._sign_up_user()
        verification_body = {
            "method": 1,
            "phoneNumber": sample_user()["phoneNumber"],
            "language": Language.EN,
            "clientId": "ctest1",
            "projectId": "ptest1",
        }
        rsp = self.flask_client.post(
            "/api/auth/v1beta/sendverificationtoken", json=verification_body
        )
        self.assertEqual(rsp.status_code, 200)


class SignInWithPhoneTestCase(BaseSignUpTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.sms_adapter.code = "878008"

    def test_a_valid_verification_token(self):
        self._sign_up_user()
        rsp = self.flask_client.post(
            "/api/auth/v1beta/signin",
            json={
                "method": 1,
                "phoneNumber": sample_user()["phoneNumber"],
                "confirmationCode": "878008",
                "clientId": "ctest1",
                "projectId": "ptest1",
            },
            environ_base={},
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertIsNotNone(rsp.json["refreshToken"])
        claims = jwt.decode(rsp.json["refreshToken"], verify=False)
        self.assertEqual(claims["userClaims"]["projectId"], sample_user()["projectId"])
        self.assertEqual(claims["userClaims"]["clientId"], sample_user()["clientId"])
        self.assertEqual(claims["userClaims"]["method"], Method.PHONE_NUMBER)

        uid = rsp.json["uid"]
        rsp = self.flask_client.get(f"/api/auth/v1beta/user/{uid}/sessions")
        self.assertEqual(1, len(rsp.json))

    def test_an_invalid_verification_token(self):
        self._sign_up_user()
        rsp = self.flask_client.post(
            "/api/auth/v1beta/signin",
            json={
                "method": 1,
                "phoneNumber": sample_user()["phoneNumber"],
                "confirmationCode": "0000000",
                "clientId": "ctest1",
                "projectId": "ptest1",
            },
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(rsp.json["code"], ErrorCodes.INVALID_VERIFICATION_CODE)


class RefreshTokenTestCase(BaseSignUpTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.sms_adapter.code = "878008"

    def setUp(self):
        super().setUp()
        self.uid = self._sign_up_user()
        self.refreshToken = self.flask_client.post(
            "/api/auth/v1beta/signin",
            json={
                "method": 1,
                "phoneNumber": sample_user()["phoneNumber"],
                "confirmationCode": "878008",
                "clientId": "ctest1",
                "projectId": "ptest1",
            },
        ).json["refreshToken"]

    def test_a_valid_refresh_token(self):
        rsp = self.flask_client.post(
            "/api/auth/v1beta/refreshtoken", json={"refreshToken": self.refreshToken}
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertIsNotNone(rsp.json["authToken"])
        claims = jwt.decode(rsp.json["authToken"], verify=False)
        self.assertEqual(claims["userClaims"]["projectId"], sample_user()["projectId"])
        self.assertEqual(claims["userClaims"]["clientId"], sample_user()["clientId"])
        self.assertEqual(claims["userClaims"]["method"], Method.PHONE_NUMBER)
        self.assertIsNotNone(rsp.json["expiresIn"])

        rsp = self.flask_client.post(
            "/api/auth/v1beta/authprofile", json={"authToken": rsp.json["authToken"]}
        )
        uid = rsp.json["uid"]
        rsp = self.flask_client.get(f"/api/auth/v1beta/user/{uid}/sessions")
        self.assertGreaterEqual(
            rsp.json[0]["updateDateTime"], rsp.json[0]["createDateTime"]
        )

    def test_refresh_token_with_email_and_password(self):
        email = "usertest+single@test.com"
        password = "343$#31123fdFD"
        res = self.flask_client.post(
            "/api/auth/v1/signin",
            json={
                "method": Method.EMAIL_PASSWORD,
                "email": email,
                "password": password,
                "clientId": "ctest1",
                "projectId": "ptest1",
            },
        )
        refresh_token = res.json["refreshToken"]

        # with and password
        payload = {
            RefreshTokenRequestObjectV1.REFRESH_TOKEN: refresh_token,
            RefreshTokenRequestObjectV1.EMAIL: email,
            RefreshTokenRequestObjectV1.PASSWORD: password,
        }
        rsp = self.flask_client.post("/api/auth/v1/refreshtoken", json=payload)
        self.assertEqual(rsp.status_code, 200)
        new_refresh_token = rsp.json.get(RefreshTokenResponseObject.REFRESH_TOKEN)
        self.assertIsNotNone(new_refresh_token)
        self.assertEqual(new_refresh_token, refresh_token)

        # with invalid password
        rsp = self.flask_client.post(
            "/api/auth/v1/refreshtoken",
            json={
                **payload,
                RefreshTokenRequestObjectV1.PASSWORD: "343$#31123fdFDXCVXCVX",
            },
        )
        self.assertEqual(rsp.status_code, 403)
        self.assertEqual(rsp.json["code"], 100012)

    def test_refresh_token_with_email_and_password_mfa(self):
        config = self.test_server.config.server
        client = config.project.get_client_by_id("ctest1")
        client.accessTokenExpiresAfterMinutes = 15
        config.testEnvironment = True  # allow test verification code

        email = "usertest+single@test.com"
        password = "343$#31123fdFD"
        # sign in SFA
        res = self.flask_client.post(
            "/api/auth/v1/signin",
            json={
                "method": Method.TWO_FACTOR_AUTH,
                "email": email,
                "password": password,
                "clientId": "ctest1",
                "projectId": "ptest1",
            },
        )
        sfa_refresh_token = res.json["refreshToken"]

        # sign in MFA
        res = self.flask_client.post(
            "/api/auth/v1/signin",
            json={
                "method": Method.TWO_FACTOR_AUTH,
                "refreshToken": sfa_refresh_token,
                "confirmationCode": "010101",
                "clientId": "ctest1",
                "projectId": "ptest1",
            },
        )
        mfa_refresh_token = res.json["refreshToken"]
        with freeze_time(datetime.utcnow() + timedelta(minutes=15)):
            payload = {RefreshTokenRequestObjectV1.REFRESH_TOKEN: mfa_refresh_token}
            rsp = self.flask_client.post("/api/auth/v1/refreshtoken", json=payload)
            self.assertEqual(rsp.status_code, 401)
            self.assertEqual(rsp.json["code"], ErrorCodes.SESSION_TIMEOUT)

            payload = {
                RefreshTokenRequestObjectV1.REFRESH_TOKEN: mfa_refresh_token,
                RefreshTokenRequestObjectV1.EMAIL: email,
                RefreshTokenRequestObjectV1.PASSWORD: password,
            }

            rsp = self.flask_client.post("/api/auth/v1/refreshtoken", json=payload)
            self.assertEqual(rsp.status_code, 200)
            self.assertIn("authToken", rsp.json)
            new_refresh_token = rsp.json.get(RefreshTokenResponseObject.REFRESH_TOKEN)
            self.assertIsNotNone(new_refresh_token)
            # Check to see if refresh token in response has been updated
            self.assertNotEqual(new_refresh_token, mfa_refresh_token)

    def test_an_invalid_refresh_token(self):
        rsp = self.flask_client.post(
            "/api/auth/v1beta/refreshtoken",
            json={"refreshToken": self.refreshToken + "test"},
        )
        self.assertEqual(rsp.status_code, 401)


class AuthProfileTestCase(BaseSignUpTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.sms_adapter.code = "878008"

    def setUp(self):
        super().setUp()
        self.uid = self._sign_up_user()
        self.refreshToken = self.flask_client.post(
            "/api/auth/v1beta/signin",
            json={
                "method": 1,
                "phoneNumber": sample_user()["phoneNumber"],
                "confirmationCode": "878008",
                "clientId": "ctest1",
                "projectId": "ptest1",
            },
        ).json["refreshToken"]
        self.authToken = self.flask_client.post(
            "/api/auth/v1beta/refreshtoken", json={"refreshToken": self.refreshToken}
        ).json["authToken"]

    def test_a_valid_auth_token(self):
        rsp = self.flask_client.post(
            "/api/auth/v1beta/authprofile", json={"authToken": self.authToken}
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(rsp.json["uid"], self.uid)

    def test_an_invalid_auth_token(self):
        rsp = self.flask_client.post(
            "/api/auth/v1beta/authprofile", json={"authToken": self.authToken + "test"}
        )
        self.assertEqual(rsp.status_code, 401)


class RetrieveSessionsTestCase(BaseSignUpTestCase):
    fixtures = [Path(__file__).parent.joinpath("fixtures/session_dump.json")]

    def test_retrieve_device_sessions_by_user_id(self):
        uid = "5eafc4cf573e3f55ee088e1c"
        rsp = self.flask_client.get(f"/api/auth/v1beta/user/{uid}/sessions")
        self.assertEqual(1, len(rsp.json))

    def test_retrieve_device_sessions_by_invalid_user_id(self):
        uid = "5eafc4cf573e3f55ee088e1a"
        rsp = self.flask_client.get(f"/api/auth/v1beta/user/{uid}/sessions")
        self.assertEqual(0, len(rsp.json))


class SignOutTestCase(BaseSignUpTestCase):
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/mfa_user_dump.json"),
        Path(__file__).parent.joinpath("fixtures/session_dump.json"),
    ]
    uid = "5eafc4cf573e3f55ee088e1c"

    REFRESH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1ODk0NDkyMjUsIm5iZiI6MTU4OTQ0OTIyNSwianRpIjoiOTIxMmZlNWYtYjhmMi00NjMyLThlM2UtMzhlMDUzMGE3NDMxIiwiZXhwIjoxNTg5NTM1NjI1LCJpZGVudGl0eSI6IjVlYWZjNGNmNTczZTNmNTVlZTA4OGUxYyIsImZyZXNoIjpmYWxzZSwidHlwZSI6ImFjY2VzcyIsImF1ZCI6InVybjptcCIsInVzZXJDbGFpbXMiOnsicHJvamVjdElkIjoicDEiLCJjbGllbnRJZCI6ImMxIiwibWV0aG9kIjoiZW1haWxfcGFzc3dvcmRsZXNzIiwiZW1haWxWZXJpZmllZCI6ZmFsc2V9fQ.DZcBhJUfMWqmhb9v9cBabEAf5AfslMaowQKw3NeXUyY"
    DEVICE_PUSH_ID = "cp8tp-XcRjCTPe5NIVsxbr:APA91bGC8igi6XNehsmoWIJfN-loX9eoma2_sRW197dlVoVbrKuchmfwXLpLaOsF9uGdtgNWZMTz8v_dkb-WLOdeRr_hHXX-PNn5ELhlmb1w9XG92aSMH-GeMRyArcBU8CmPx-012EbR"
    VOIP_DEVICE_PUSH_ID = "cp8tp-XcRjCTPe5NIVsxbr:APA91bGC8igi6XNehsmoWIJfN-loX9eoma2_sRW197dlVoVbrKuchmfwXLpLaOsF9uGdtgNWZMTz8v_dkb-WLOdeRr_hHXX-PNn5ELhlmb1w9XG92aSMH-GeMRyArcBU8CmPx-999EaR"

    def post(
        self, body: dict, environ_base: dict = None, version: str = "v1beta"
    ) -> TestResponse:
        if environ_base is None:
            environ_base = {"HTTP_USER_AGENT": "werkzeug/1.0.1"}
        url = f"/api/auth/{version}/signout"
        return self.flask_client.post(url, json=body, environ_base=environ_base)

    def test_failure_emtpy_http_user_agent(self):
        rsp = self.post({SignOutRequestObject.USER_ID: self.uid}, {})
        self.assertEqual(400, rsp.status_code)

    def test_sign_out(self):
        rsp = self.post({SignOutRequestObject.USER_ID: self.uid})
        self.assertEqual(200, rsp.status_code)
        self.assertIsNotNone(rsp.json["id"])
        rsp = self.flask_client.get(f"/api/auth/v1beta/user/{self.uid}/sessions")
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, len(rsp.json))

    def test_sign_out_invalid_user_id(self):
        rsp = self.post({SignOutRequestObject.USER_ID: "5eafc4cf573e3f55ee088e1a"})
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(100049, rsp.json["code"])

    def test_sign_out_when_already_signed_out(self):
        rsp = self.post({SignOutRequestObject.USER_ID: self.uid})
        self.assertEqual(200, rsp.status_code)
        rsp = self.post({SignOutRequestObject.USER_ID: self.uid})
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100014, rsp.json["code"])

    def test_sign_out_v1(self):
        user_id = "5e8f0c74b50aa9656c34789a"
        rsp = self.post(
            body={
                SignOutRequestObjectV1.USER_ID: user_id,
                SignOutRequestObjectV1.REFRESH_TOKEN: self.REFRESH_TOKEN,
                SignOutRequestObjectV1.DEVICE_PUSH_ID: self.DEVICE_PUSH_ID,
            },
            version="v1",
        )
        self.assertEqual(200, rsp.status_code)

        session = self._filter_user_sessions(user_id, rsp.json["id"])
        self.assertEqual(False, session[DeviceSessionV1.IS_ACTIVE])
        self.assertIsNotNone(session[DeviceSessionV1.REFRESH_TOKEN])

        user_data = self.mongo_database[USER_COLLECTION].find_one(
            {"_id": ObjectId(user_id)}
        )
        auth_user: AuthUser = AuthUser.from_dict(user_data)
        self.assertEqual(
            auth_user.has_mfa_identifier(AuthIdentifierType.DEVICE_TOKEN), True
        )

    def test_sign_out_voip_device_push_id_v1(self):
        user_id = "5e8f0c74b50aa9656c34789a"
        rsp = self.post(
            body={
                SignOutRequestObjectV1.USER_ID: user_id,
                SignOutRequestObjectV1.REFRESH_TOKEN: self.REFRESH_TOKEN,
                SignOutRequestObjectV1.VOIP_DEVICE_PUSH_ID: self.VOIP_DEVICE_PUSH_ID,
            },
            version="v1",
        )
        self.assertEqual(200, rsp.status_code)

        session = self._filter_user_sessions(user_id, rsp.json["id"])
        self.assertEqual(False, session[DeviceSessionV1.IS_ACTIVE])
        self.assertIsNotNone(session[DeviceSessionV1.REFRESH_TOKEN])

        user_data = self.mongo_database[USER_COLLECTION].find_one(
            {"_id": ObjectId(user_id)}
        )
        auth_user: AuthUser = AuthUser.from_dict(user_data)
        self.assertEqual(
            auth_user.has_mfa_identifier(AuthIdentifierType.DEVICE_TOKEN), True
        )

    def test_sign_out_v1_clears_mfa(self):
        user_id = "5e8f0c74b50aa9656c34789a"
        rsp = self.post(
            body={
                SignOutRequestObjectV1.USER_ID: user_id,
                SignOutRequestObjectV1.REFRESH_TOKEN: self.REFRESH_TOKEN,
                SignOutRequestObjectV1.DEVICE_PUSH_ID: self.DEVICE_PUSH_ID,
                SignOutRequestObjectV1.DEVICE_TOKEN: "sample_device_token",
            },
            version="v1",
        )
        self.assertEqual(200, rsp.status_code)

        session = self._filter_user_sessions(user_id, rsp.json["id"])
        self.assertEqual(False, session[DeviceSessionV1.IS_ACTIVE])
        self.assertIsNotNone(session[DeviceSessionV1.REFRESH_TOKEN])

        user_data = self.mongo_database[USER_COLLECTION].find_one(
            {"_id": ObjectId(user_id)}
        )
        auth_user: AuthUser = AuthUser.from_dict(user_data)
        self.assertEqual(
            auth_user.has_mfa_identifier(AuthIdentifierType.DEVICE_TOKEN), False
        )

    def _filter_user_sessions(self, user_id: str, session_id: str):
        sessions = self.mongo_database[SESSION_COLLECTION].find(
            {DeviceSessionV1.USER_ID: ObjectId(user_id)}
        )
        return next(
            filter(
                lambda session: session[DeviceSessionV1.ID_] == ObjectId(session_id),
                sessions,
            )
        )


class TFATestCase(BaseSignUpTestCase):
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/mfa_user_dump.json"),
    ]

    @classmethod
    def setUpClass(cls) -> None:
        super(TFATestCase, cls).setUpClass()
        cls.token_adapter: TokenAdapter = inject.instance(TokenAdapter)

    def check_tokens_valid_for_mfa(
        self, auth_token=None, refresh_token=None, valid=True
    ):
        if auth_token:
            decoded_auth_token = self.token_adapter.verify_token(auth_token, "access")
            auth_stage = decoded_auth_token[USER_CLAIMS_KEY][AUTH_STAGE]
            auth_stage_equal = auth_stage == AuthStage.SECOND
            self.assertEqual(auth_stage_equal, valid)
        if refresh_token:
            decoded_ref_token = self.token_adapter.verify_token(
                refresh_token, "refresh"
            )
            ref_auth_stage = decoded_ref_token[USER_CLAIMS_KEY][AUTH_STAGE]
            refresh_stage_equal = ref_auth_stage == AuthStage.SECOND
            self.assertEqual(refresh_stage_equal, valid)

    def check_user_eligible_for_mfa(self, email=None, phone_number=None, eligible=True):
        check_auth_attributes_data = {
            CheckAuthAttributesRequestObject.PHONE_NUMBER: phone_number,
            CheckAuthAttributesRequestObject.EMAIL: email,
            CheckAuthAttributesRequestObject.CLIENT_ID: CLIENT_ID_3,
            CheckAuthAttributesRequestObject.PROJECT_ID: PROJECT_ID,
        }
        check_auth_response = self.flask_client.post(
            "/api/auth/v1beta/check-auth-attributes",
            json=remove_none_values(check_auth_attributes_data),
        )
        self.assertEqual(200, check_auth_response.status_code)
        self.assertEqual(check_auth_response.json.get("eligibleForMFA"), eligible)

    def test_new_user_mfa_signup_and_signin(self):
        # 1. Sign up
        new_user_email = NOT_EXISTING_EMAIL
        new_user_phone_number = "+380500000000"
        signup_data = {
            SignUpRequestObject.METHOD: Method.TWO_FACTOR_AUTH,
            SignUpRequestObject.EMAIL: new_user_email,
            SignUpRequestObject.PASSWORD: USER_PASSWORD,
            SignUpRequestObject.DISPLAY_NAME: "test",
            SignUpRequestObject.VALIDATION_DATA: {"activationCode": "53924415"},
            SignUpRequestObject.USER_ATTRIBUTES: {
                "familyName": "hey",
                "givenName": "test",
                "dob": "1988-02-20",
                "gender": "MALE",
            },
            SignUpRequestObject.CLIENT_ID: "ctest1",
            SignUpRequestObject.PROJECT_ID: "ptest1",
        }

        sign_up_response = self.flask_client.post(
            "/api/auth/v1beta/signup", json=signup_data
        )
        self.assertEqual(200, sign_up_response.status_code)

        # 2. Send email confirmation
        send_email_confirmation_data = {
            SendVerificationTokenRequestObject.METHOD: SendVerificationTokenMethod.EMAIL_SIGNUP_CONFIRMATION,
            SendVerificationTokenRequestObject.EMAIL: new_user_email,
            SendVerificationTokenRequestObject.CLIENT_ID: "ctest1",
            SendVerificationTokenRequestObject.PROJECT_ID: "ptest1",
        }
        send_email_confirmation_response = self.flask_client.post(
            "/api/auth/v1beta/sendverificationtoken", json=send_email_confirmation_data
        )
        self.assertEqual(200, send_email_confirmation_response.status_code)

        # 3. Confirm email with code from email
        email_confirmation_data = {
            ConfirmationRequestObject.EMAIL: new_user_email,
            ConfirmationRequestObject.CONFIRMATION_CODE: "123",
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
        }
        email_confirmation_response = self.flask_client.post(
            "/api/auth/v1beta/confirm", json=email_confirmation_data, environ_base={}
        )
        self.assertEqual(200, email_confirmation_response.status_code)
        refresh_token = email_confirmation_response.json.get("refreshToken")
        auth_token = email_confirmation_response.json.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)
        # Confirming tokens are not valid for MFA
        self.check_tokens_valid_for_mfa(auth_token, refresh_token, valid=False)

        # 4. Set auth attributes with auth token from confirmation email step
        set_auth_attributes_data = {
            SetAuthAttributesRequestObject.PHONE_NUMBER: new_user_phone_number,
            SetAuthAttributesRequestObject.AUTH_TOKEN: auth_token,
            SetAuthAttributesRequestObject.CLIENT_ID: CLIENT_ID_3,
            SetAuthAttributesRequestObject.PROJECT_ID: PROJECT_ID,
        }
        set_auth_attributes_response = self.flask_client.post(
            "/api/auth/v1beta/set-auth-attributes", json=set_auth_attributes_data
        )
        self.assertEqual(200, set_auth_attributes_response.status_code)

        # 5. Send phone number confirmation
        send_phone_number_confirmation_data = {
            SendVerificationTokenRequestObject.METHOD: SendVerificationTokenMethod.PHONE_NUMBER,
            SendVerificationTokenRequestObject.PHONE_NUMBER: new_user_phone_number,
            SendVerificationTokenRequestObject.CLIENT_ID: "ctest1",
            SendVerificationTokenRequestObject.PROJECT_ID: "ptest1",
        }
        send_phone_number_confirmation_response = self.flask_client.post(
            "/api/auth/v1beta/sendverificationtoken",
            json=send_phone_number_confirmation_data,
        )
        self.assertEqual(200, send_phone_number_confirmation_response.status_code)

        # 6. Confirm phone number and get auth token from confirmation response.
        phone_number_confirmation_data = {
            ConfirmationRequestObject.PHONE_NUMBER: new_user_phone_number,
            ConfirmationRequestObject.EMAIL: new_user_email,
            ConfirmationRequestObject.CONFIRMATION_CODE: "123",
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
        }
        phone_number_confirmation_response = self.flask_client.post(
            "/api/auth/v1beta/confirm", json=phone_number_confirmation_data
        )
        self.assertEqual(200, phone_number_confirmation_response.status_code)
        refresh_token = phone_number_confirmation_response.json.get("refreshToken")
        auth_token = phone_number_confirmation_response.json.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)
        # Confirming tokens are valid for MFA
        self.check_tokens_valid_for_mfa(auth_token, refresh_token)

    def test_user_mfa_signin(self):
        # 1. Sign in with email + password as first factor
        sign_in_data = {
            SignInRequestObject.METHOD: Method.TWO_FACTOR_AUTH,
            SignInRequestObject.EMAIL: USER_EMAIL,
            SignInRequestObject.PASSWORD: USER_PASSWORD,
            SignInRequestObject.CLIENT_ID: "ctest1",
            SignInRequestObject.PROJECT_ID: "ptest1",
        }
        sign_in_response = self.flask_client.post(
            "/api/auth/v1beta/signin", json=sign_in_data
        )
        self.assertEqual(200, sign_in_response.status_code)
        refresh_token = sign_in_response.json.get("refreshToken")
        self.assertIsNotNone(refresh_token)

        # 2. Send confirmation code to user's phone number with refresh token
        send_phone_number_confirmation_data = {
            SendVerificationTokenRequestObject.METHOD: SendVerificationTokenMethod.TWO_FACTOR_AUTH,
            SendVerificationTokenRequestObject.REFRESH_TOKEN: refresh_token,
            SendVerificationTokenRequestObject.CLIENT_ID: "ctest1",
            SendVerificationTokenRequestObject.PROJECT_ID: "ptest1",
        }
        send_phone_number_confirmation_response = self.flask_client.post(
            "/api/auth/v1beta/sendverificationtoken",
            json=send_phone_number_confirmation_data,
        )
        self.assertEqual(200, send_phone_number_confirmation_response.status_code)
        masked_phone = mask_phone_number(USER_PHONE_NUMBER)
        self.assertIn("to", send_phone_number_confirmation_response.json)
        self.assertEqual(
            masked_phone, send_phone_number_confirmation_response.json["to"]
        )

        # 3. Sign in with refresh token from step 1 and code from step 2
        second_factor_sign_in_data = {
            SignInRequestObject.METHOD: Method.TWO_FACTOR_AUTH,
            SignInRequestObject.REFRESH_TOKEN: refresh_token,
            SignInRequestObject.CONFIRMATION_CODE: "123",
            SignInRequestObject.CLIENT_ID: "ctest1",
            SignInRequestObject.PROJECT_ID: "ptest1",
        }
        second_factor_sign_in_response = self.flask_client.post(
            "/api/auth/v1beta/signin", json=second_factor_sign_in_data
        )
        self.assertEqual(200, second_factor_sign_in_response.status_code)
        # Verify tokens are valid for MFA
        refresh_token = second_factor_sign_in_response.json.get("refreshToken")
        auth_token = second_factor_sign_in_response.json.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)
        self.check_tokens_valid_for_mfa(auth_token, refresh_token)

    def test_signin_same_email_uppercase(self):
        # 1. Sign in with email uppercase
        sign_in_data = {
            SignInRequestObject.METHOD: Method.TWO_FACTOR_AUTH,
            SignInRequestObject.EMAIL: USER_EMAIL.upper(),
            SignInRequestObject.PASSWORD: USER_PASSWORD,
            SignInRequestObject.CLIENT_ID: "ctest1",
            SignInRequestObject.PROJECT_ID: "ptest1",
        }
        sign_in_response = self.flask_client.post(
            "/api/auth/v1beta/signin", json=sign_in_data
        )
        self.assertEqual(200, sign_in_response.status_code)

    def test_old_user_migrate_and_sign_in_email(self):
        existing_user_with_email_only = "useremail@test.com"
        new_user_phone_number = "+380500000000"

        # 1. Sign in with email + code
        sign_in_data = {
            SignInRequestObject.METHOD: Method.EMAIL,
            SignInRequestObject.EMAIL: existing_user_with_email_only,
            SignInRequestObject.CONFIRMATION_CODE: "123",
            SignInRequestObject.CLIENT_ID: "ctest1",
            SignInRequestObject.PROJECT_ID: "ptest1",
        }
        sign_in_response = self.flask_client.post(
            "/api/auth/v1beta/signin", json=sign_in_data
        )
        self.assertEqual(200, sign_in_response.status_code)
        refresh_token = sign_in_response.json.get("refreshToken")
        auth_token = sign_in_response.json.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)

        # 2. Check that user is not eligible for MFA
        self.check_user_eligible_for_mfa(
            email=existing_user_with_email_only, eligible=False
        )

        # 3. Set missing attributes
        set_auth_attributes_data = {
            SetAuthAttributesRequestObject.PHONE_NUMBER: new_user_phone_number,
            SetAuthAttributesRequestObject.PASSWORD: "Aa123456",
            SetAuthAttributesRequestObject.AUTH_TOKEN: auth_token,
            SetAuthAttributesRequestObject.CLIENT_ID: CLIENT_ID_3,
            SetAuthAttributesRequestObject.PROJECT_ID: PROJECT_ID,
        }
        set_auth_attributes_response = self.flask_client.post(
            "/api/auth/v1beta/set-auth-attributes", json=set_auth_attributes_data
        )
        self.assertEqual(200, set_auth_attributes_response.status_code)

        # 4. Send phone number confirmation by flow
        # 5. Confirm phone number and get auth token from confirmation response.
        phone_number_confirmation_data = {
            ConfirmationRequestObject.PHONE_NUMBER: new_user_phone_number,
            ConfirmationRequestObject.EMAIL: existing_user_with_email_only,
            ConfirmationRequestObject.CONFIRMATION_CODE: "123",
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
        }
        phone_number_confirmation_response = self.flask_client.post(
            "/api/auth/v1beta/confirm", json=phone_number_confirmation_data
        )
        self.assertEqual(200, phone_number_confirmation_response.status_code)
        refresh_token = phone_number_confirmation_response.json.get("refreshToken")
        auth_token = phone_number_confirmation_response.json.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)

        # Confirming tokens are valid for MFA
        self.check_tokens_valid_for_mfa(auth_token, refresh_token)

        # Confirming that user is also eligible for MFA at this moment
        self.check_user_eligible_for_mfa(email=existing_user_with_email_only)

    def test_old_user_migrate_and_sign_in_phone_number(self):
        existing_user_with_phone_number_only = "+380500000001"
        new_user_email = "somenewuseremail@mail.com"

        # 1. Sign in with phonenumber + code
        sign_in_data = {
            SignInRequestObject.METHOD: Method.PHONE_NUMBER,
            SignInRequestObject.PHONE_NUMBER: existing_user_with_phone_number_only,
            SignInRequestObject.CONFIRMATION_CODE: "123",
            SignInRequestObject.CLIENT_ID: "ctest1",
            SignInRequestObject.PROJECT_ID: "ptest1",
        }
        sign_in_response = self.flask_client.post(
            "/api/auth/v1beta/signin", json=sign_in_data
        )
        self.assertEqual(200, sign_in_response.status_code)
        refresh_token = sign_in_response.json.get("refreshToken")
        auth_token = sign_in_response.json.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)

        # 2. Check that user is not eligible for MFA
        self.check_user_eligible_for_mfa(
            phone_number=existing_user_with_phone_number_only, eligible=False
        )

        # 3. Set missing attributes
        set_auth_attributes_data = {
            SetAuthAttributesRequestObject.EMAIL: new_user_email,
            SetAuthAttributesRequestObject.PASSWORD: "Aa123456",
            SetAuthAttributesRequestObject.AUTH_TOKEN: auth_token,
            SetAuthAttributesRequestObject.CLIENT_ID: CLIENT_ID_3,
            SetAuthAttributesRequestObject.PROJECT_ID: PROJECT_ID,
        }
        set_auth_attributes_response = self.flask_client.post(
            "/api/auth/v1beta/set-auth-attributes", json=set_auth_attributes_data
        )
        self.assertEqual(200, set_auth_attributes_response.status_code)

        # 4. Send email confirmation (4) by flow
        send_email_confirmation_data = {
            SendVerificationTokenRequestObject.METHOD: SendVerificationTokenMethod.EXISTING_USER_EMAIL_CONFIRMATION,
            SendVerificationTokenRequestObject.EMAIL: new_user_email,
            SendVerificationTokenRequestObject.CLIENT_ID: "ctest1",
            SendVerificationTokenRequestObject.PROJECT_ID: "ptest1",
        }
        send_email_confirmation_response = self.flask_client.post(
            "/api/auth/v1beta/sendverificationtoken", json=send_email_confirmation_data
        )
        self.assertEqual(200, send_email_confirmation_response.status_code)

        # 5. Confirm email and get auth token from confirmation response.
        token_adapter = inject.instance(TokenAdapter)
        confirmation_token = token_adapter.create_confirmation_token(new_user_email)
        email_confirmation_data = {
            ConfirmationRequestObject.EMAIL: new_user_email,
            ConfirmationRequestObject.CONFIRMATION_CODE: confirmation_token,
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
        }
        email_confirmation_response = self.flask_client.post(
            "/api/auth/v1beta/confirm", json=email_confirmation_data
        )
        self.assertEqual(200, email_confirmation_response.status_code)
        refresh_token = email_confirmation_response.json.get("refreshToken")
        auth_token = email_confirmation_response.json.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)

        # Confirming tokens are valid for MFA
        self.check_tokens_valid_for_mfa(auth_token, refresh_token)

        # Confirming that user is also eligible for MFA at this moment
        self.check_user_eligible_for_mfa(
            phone_number=existing_user_with_phone_number_only
        )

    def test_device_token_attribute(self):
        existing_user_with_phone_number_only = "+380500000001"

        # 1. Sign in with phonenumber + code
        sign_in_data = {
            SignInRequestObject.METHOD: Method.PHONE_NUMBER,
            SignInRequestObject.PHONE_NUMBER: existing_user_with_phone_number_only,
            SignInRequestObject.CONFIRMATION_CODE: "123",
            SignInRequestObject.CLIENT_ID: "ctest1",
            SignInRequestObject.PROJECT_ID: "ptest1",
        }
        sign_in_response = self.flask_client.post(
            "/api/auth/v1beta/signin", json=sign_in_data
        )
        self.assertEqual(200, sign_in_response.status_code)
        refresh_token = sign_in_response.json.get("refreshToken")
        auth_token = sign_in_response.json.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)

        # 2. Check that user is not eligible for MFA
        self.check_user_eligible_for_mfa(
            phone_number=existing_user_with_phone_number_only, eligible=False
        )

        device_token = "device token"
        # 3. Set missing attributes
        set_auth_attributes_data = {
            SetAuthAttributesRequestObject.DEVICE_TOKEN: device_token,
            SetAuthAttributesRequestObject.AUTH_TOKEN: auth_token,
            SetAuthAttributesRequestObject.CLIENT_ID: CLIENT_ID_3,
            SetAuthAttributesRequestObject.PROJECT_ID: PROJECT_ID,
        }
        set_auth_attributes_response = self.flask_client.post(
            "/api/auth/v1beta/set-auth-attributes", json=set_auth_attributes_data
        )
        self.assertEqual(200, set_auth_attributes_response.status_code)

        user_data = self.mongo_database[USER_COLLECTION].find_one(
            {"_id": ObjectId(set_auth_attributes_response.json["uid"])}
        )
        auth_user: AuthUser = AuthUser.from_dict(user_data)
        self.assertIsNotNone(
            auth_user.get_mfa_identifier(AuthIdentifierType.DEVICE_TOKEN, device_token)
        )

        set_auth_attributes_response = self.flask_client.post(
            "/api/auth/v1beta/set-auth-attributes", json=set_auth_attributes_data
        )
        self.assertEqual(200, set_auth_attributes_response.status_code)

        new_user_data = self.mongo_database[USER_COLLECTION].find_one(
            {"_id": ObjectId(set_auth_attributes_response.json["uid"])}
        )
        self.assertListEqual(
            user_data[AuthUser.MFA_IDENTIFIERS], new_user_data[AuthUser.MFA_IDENTIFIERS]
        )

    def test_user_mfa_signin_v1_remember_me(self):
        client_id = "ctest1"
        project_id = "ptest1"
        # 1. Sign in with email + password as first factor
        sign_in_data = {
            SignInRequestObjectV1.METHOD: Method.TWO_FACTOR_AUTH,
            SignInRequestObjectV1.EMAIL: USER_EMAIL,
            SignInRequestObjectV1.PASSWORD: USER_PASSWORD,
            SignInRequestObjectV1.CLIENT_ID: client_id,
            SignInRequestObjectV1.PROJECT_ID: project_id,
        }
        sign_in_response = self.flask_client.post(
            "/api/auth/v1/signin", json=sign_in_data
        )
        self.assertEqual(200, sign_in_response.status_code)
        refresh_token = sign_in_response.json.get("refreshToken")
        self.assertIsNotNone(refresh_token)

        # 2. Send confirmation code to user's phone number with refresh token
        send_phone_number_confirmation_data = {
            SendVerificationTokenRequestObject.METHOD: SendVerificationTokenMethod.TWO_FACTOR_AUTH,
            SendVerificationTokenRequestObject.REFRESH_TOKEN: refresh_token,
            SendVerificationTokenRequestObject.CLIENT_ID: client_id,
            SendVerificationTokenRequestObject.PROJECT_ID: project_id,
        }
        send_phone_number_confirmation_response = self.flask_client.post(
            "/api/auth/v1beta/sendverificationtoken",
            json=send_phone_number_confirmation_data,
        )
        self.assertEqual(200, send_phone_number_confirmation_response.status_code)
        masked_phone = mask_phone_number(USER_PHONE_NUMBER)
        self.assertIn("to", send_phone_number_confirmation_response.json)
        self.assertEqual(
            masked_phone, send_phone_number_confirmation_response.json["to"]
        )

        # 3. Sign in with refresh token from step 1 and code from step 2
        second_factor_sign_in_data = {
            SignInRequestObjectV1.METHOD: Method.TWO_FACTOR_AUTH,
            SignInRequestObjectV1.REFRESH_TOKEN: refresh_token,
            SignInRequestObjectV1.CONFIRMATION_CODE: "123",
            SignInRequestObjectV1.CLIENT_ID: client_id,
            SignInRequestObjectV1.PROJECT_ID: project_id,
        }
        second_factor_sign_in_response = self.flask_client.post(
            "/api/auth/v1/signin", json=second_factor_sign_in_data
        )
        self.assertEqual(200, second_factor_sign_in_response.status_code)
        # Verify tokens are valid for MFA
        refresh_token = second_factor_sign_in_response.json.get("refreshToken")
        auth_token = second_factor_sign_in_response.json.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)
        self.check_tokens_valid_for_mfa(auth_token, refresh_token)

        # check refreshtoken with device token
        device_token = "device token"
        set_auth_attributes_data = {
            SetAuthAttributesRequestObject.DEVICE_TOKEN: device_token,
            SetAuthAttributesRequestObject.AUTH_TOKEN: auth_token,
            SetAuthAttributesRequestObject.CLIENT_ID: client_id,
            SetAuthAttributesRequestObject.PROJECT_ID: project_id,
        }
        set_auth_attributes_response = self.flask_client.post(
            "/api/auth/v1beta/set-auth-attributes", json=set_auth_attributes_data
        )
        self.assertEqual(200, set_auth_attributes_response.status_code)

        refresh_token_response = self.flask_client.post(
            "/api/auth/v1/refreshtoken",
            json={"refreshToken": refresh_token, "deviceToken": device_token},
        )
        self.assertEqual(200, refresh_token_response.status_code)
        updated_refresh_token = refresh_token_response.json.get("refreshToken")
        # Verify tokens are valid for MFA
        self.check_tokens_valid_for_mfa(
            refresh_token_response.json.get("authToken"), updated_refresh_token
        )

        # remember me duration
        second_factor_sign_in_data = {
            SignInRequestObjectV1.METHOD: Method.TWO_FACTOR_AUTH,
            SignInRequestObjectV1.REFRESH_TOKEN: updated_refresh_token,
            SignInRequestObjectV1.EMAIL: USER_EMAIL,
            SignInRequestObjectV1.PASSWORD: USER_PASSWORD,
            SignInRequestObjectV1.CLIENT_ID: client_id,
            SignInRequestObjectV1.PROJECT_ID: project_id,
        }
        after_a_week = datetime.utcnow() + timedelta(minutes=30)
        with freeze_time(after_a_week):
            remember_response = self.flask_client.post(
                "/api/auth/v1/signin", json=second_factor_sign_in_data
            )
            self.assertEqual(200, remember_response.status_code)
            # Verify tokens are valid for MFA
            remember_refresh_token = remember_response.json.get("refreshToken")
            remember_auth_token = remember_response.json.get("authToken")
            self.assertIsNotNone(remember_refresh_token)
            self.assertIsNotNone(remember_auth_token)
            # Verify if refreshtoken expiresIn not renewed
            self.assertGreater(
                second_factor_sign_in_response.json["expiresIn"] - 30 * 60,
                remember_response.json["expiresIn"],
            )
            self.check_tokens_valid_for_mfa(remember_auth_token, remember_refresh_token)

            # confirming you still can refresh token with updated token
            refresh_token_response = self.flask_client.post(
                "/api/auth/v1/refreshtoken",
                json={
                    "refreshToken": remember_refresh_token,
                    "deviceToken": device_token,
                },
            )
            self.assertEqual(200, refresh_token_response.status_code)


if __name__ == "__main__":
    unittest.main()
