from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from bson import ObjectId
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from sdk.auth.component import AuthComponent
from sdk.auth.enums import Method
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.use_case.auth_request_objects import (
    RefreshTokenRequestObject,
    ConfirmationRequestObject,
)
from sdk.auth.use_case.auth_response_objects import SetAuthAttributesResponseObject
from sdk.common.adapter.email_confirmation_adapter import EmailConfirmationAdapter
from sdk.common.adapter.email_verification_adapter import EmailVerificationAdapter
from sdk.common.adapter.token_adapter import TokenType
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.notification.component import NotificationComponent
from sdk.phoenix.config.server_config import Client
from sdk.tests.auth.test_helpers import (
    send_verification_token,
    email_sign_in_request,
    get_auth_token,
    request_auth_attributes,
    set_auth_attributes,
    CONFIRMATION_CODE,
    USER_PASSWORD,
    USER_EMAIL,
    PROJECT_ID,
    USER_ID,
    phone_number_sign_in_request,
)
from sdk.tests.test_case import SdkTestCase
from sdk.tests.auth.mock_objects import MockSmsAdapter, MockEmailAdapter


def get_mock_email_password_adapter():
    adapter = MagicMock()
    adapter.send_confirmation_email.return_value = None
    adapter.verify_code.return_value = True
    return adapter


class AuthAttributesTestCase(SdkTestCase):
    components = [AuthComponent(), NotificationComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/auth_users_dump.json")]
    override_config = {
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
            },
            {
                Client.NAME: "USER_ANDROID-client",
                Client.CLIENT_ID: "ctest1",
                Client.CLIENT_TYPE: "USER_ANDROID",
            },
        ],
    }
    email_adapter = None
    sms_adapter = None
    mocked_email_confirmation_adapter = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.mocked_email_confirmation_adapter = get_mock_email_password_adapter()
        cls.email_adapter = MockEmailAdapter()
        cls.sms_adapter = MockSmsAdapter()

        def configure_with_binder(binder: Binder):
            binder.bind(EmailVerificationAdapter, MockEmailAdapter(CONFIRMATION_CODE))
            binder.bind(EmailConfirmationAdapter, cls.mocked_email_confirmation_adapter)
            binder.bind("aliCloudSmsVerificationAdapter", cls.sms_adapter)
            binder.bind("twilioSmsVerificationAdapter", cls.sms_adapter)

        inject.get_injector_or_die().rebind(configure_with_binder)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        inject.clear()

    def tearDown(self):
        self.mocked_email_confirmation_adapter.reset_mock()
        return super().tearDown()

    def sign_in(self):
        rsp = send_verification_token(self.flask_client, 0, USER_EMAIL)
        self.assertEqual(rsp.status_code, 200)
        rsp = email_sign_in_request(self.flask_client, USER_EMAIL, CONFIRMATION_CODE)
        self.assertEqual(rsp.status_code, 200)
        auth_token = get_auth_token(self.flask_client, rsp.json["refreshToken"])
        return auth_token, rsp.json["refreshToken"]

    def set_pass(self, token: str, old_pass: str, new_pass: str):
        return set_auth_attributes(
            self.flask_client,
            token,
            password=new_pass,
            old_password=old_pass,
            token_type=TokenType.REFRESH.string_value,
        )

    def request_devices(self, auth_token: str = None, refresh_token: str = None):
        if not auth_token:
            auth_token = get_auth_token(self.flask_client, refresh_token)
        headers = {"Authorization": "Bearer {}".format(auth_token)}
        return self.flask_client.get("/api/notification/v1beta/device", headers=headers)

    def refresh_token(self, refresh_token: str):
        return self.flask_client.post(
            "/api/auth/v1beta/refreshtoken",
            json={RefreshTokenRequestObject.REFRESH_TOKEN: refresh_token},
        )

    def test_success_refresh_token_empty_http_user_agent(self):
        rsp = email_sign_in_request(self.flask_client, USER_EMAIL, CONFIRMATION_CODE)
        rsp = self.flask_client.post(
            "/api/auth/v1beta/refreshtoken",
            json={RefreshTokenRequestObject.REFRESH_TOKEN: rsp.json["refreshToken"]},
            environ_base={},
        )
        self.assertEqual(rsp.status_code, 200)

    def test_check_auth_attributes(self):
        auth_token, _ = self.sign_in()

        rsp = request_auth_attributes(self.flask_client, auth_token)
        self.assertEqual(rsp.json["passwordSet"], False)
        self.assertEqual(rsp.json["emailVerified"], True)
        self.assertIsNone(rsp.json.get("phoneNumber"))
        self.assertEqual(rsp.json["email"], USER_EMAIL)

    def test_set_auth_attributes(self):
        auth_token, _ = self.sign_in()

        test_phone_number = "+441347722096"
        set_auth_attributes(
            self.flask_client,
            auth_token,
            phone_number=test_phone_number,
            password=USER_PASSWORD,
        )

        rsp = request_auth_attributes(self.flask_client, auth_token)
        self.assertEqual(rsp.json["passwordSet"], True)
        self.assertEqual(rsp.json["emailVerified"], True)
        self.assertEqual(rsp.json["phoneNumber"], test_phone_number)
        self.assertEqual(rsp.json["email"], USER_EMAIL)

        # testing that still may re set while it's not verified
        new_number = "+380500000000"
        set_auth_attributes(self.flask_client, auth_token, phone_number=new_number)
        rsp = request_auth_attributes(self.flask_client, auth_token)
        self.assertEqual(rsp.json["phoneNumber"], new_number)

    def test_success_set_auth_attributes_update_verified_phone_number(self):
        initial_phone_number = "+441347722095"
        rsp = phone_number_sign_in_request(
            self.flask_client, initial_phone_number, CONFIRMATION_CODE
        )
        self.assertEqual(rsp.status_code, 200)
        auth_token = rsp.json["authToken"]

        # trying to update user attr that has verified phone number
        new_number = "+380500000000"
        rsp = send_verification_token(
            flask_client=self.flask_client,
            method=Method.PHONE_NUMBER,
            phone_number=new_number,
            client_id="ctest1",
        )
        self.assertEqual(rsp.status_code, 200)
        set_auth_attributes(
            self.flask_client,
            auth_token,
            phone_number=new_number,
            confirmation_code=CONFIRMATION_CODE,
        )
        rsp = request_auth_attributes(self.flask_client, auth_token)
        self.assertEqual(rsp.json["phoneNumber"], new_number)

    def test_failure_set_auth_attributes_update_verified_phone_number_use_same_phone_number(
        self,
    ):
        initial_phone_number = "+441347722095"
        rsp = phone_number_sign_in_request(
            self.flask_client, initial_phone_number, CONFIRMATION_CODE
        )
        self.assertEqual(rsp.status_code, 200)
        auth_token = rsp.json["authToken"]

        # trying to update with the same phone number
        rsp = send_verification_token(
            flask_client=self.flask_client,
            method=Method.PHONE_NUMBER,
            phone_number=initial_phone_number,
            client_id="ctest1",
        )
        self.assertEqual(rsp.status_code, 200)
        rsp = set_auth_attributes(
            self.flask_client,
            auth_token,
            phone_number=initial_phone_number,
            confirmation_code=CONFIRMATION_CODE,
        )
        self.assertEqual(rsp.json["code"], ErrorCodes.PHONE_NUMBER_ALREADY_SET)

    def test_failure_set_auth_attributes_update_verified_phone_number__no_confirmation_code_provided(
        self,
    ):
        initial_phone_number = "+441347722095"
        rsp = phone_number_sign_in_request(
            self.flask_client, initial_phone_number, CONFIRMATION_CODE
        )
        self.assertEqual(rsp.status_code, 200)
        auth_token = rsp.json["authToken"]

        # trying to update user attr that has verified phone number
        new_number = "+380500000000"
        rsp = set_auth_attributes(
            self.flask_client, auth_token, phone_number=new_number
        )
        res = rsp.json
        self.assertEqual(res["code"], ErrorCodes.CONFIRMATION_CODE_IS_MISSING)

    def test_set_password_updates_password_update_datetime(self):
        auth_token, refresh_token = self.sign_in()

        # checking current update password datetime
        user_query = {AuthUser.ID_: ObjectId(USER_ID)}
        user = self.mongo_database["authuser"].find_one(user_query)
        password_update_datetime = user.get(AuthUser.PASSWORD_UPDATE_DATE_TIME)
        password_create_datetime = user.get(AuthUser.PASSWORD_CREATE_DATE_TIME)
        self.assertIsNone(password_update_datetime)
        self.assertIsNone(password_create_datetime)

        set_auth_attributes(self.flask_client, auth_token, password=USER_PASSWORD)

        user = self.mongo_database["authuser"].find_one(user_query)
        new_update_date_time = user.get(AuthUser.PASSWORD_UPDATE_DATE_TIME)
        new_create_date_time = user.get(AuthUser.PASSWORD_CREATE_DATE_TIME)
        self.assertIsNotNone(new_update_date_time)
        self.assertNotEqual(password_update_datetime, new_update_date_time)
        self.assertEqual(new_create_date_time, new_update_date_time)
        self.set_pass(refresh_token, USER_PASSWORD, "someNewPass1")

        user = self.mongo_database["authuser"].find_one(user_query)
        new_update_date_time = user.get(AuthUser.PASSWORD_UPDATE_DATE_TIME)
        new_create_date_time = user.get(AuthUser.PASSWORD_CREATE_DATE_TIME)
        self.assertNotEqual(new_create_date_time, new_update_date_time)

    def test_update_to_recent_password_raises_exception(self):
        auth_token, refresh_token = self.sign_in()

        pass_1 = "Aa123456"
        pass_2 = "Aa223456"
        pass_3 = "Aa323456"
        pass_4 = "Aa423456"
        rsp = set_auth_attributes(self.flask_client, auth_token, password=pass_1)
        self.assertEqual(200, rsp.status_code)
        rsp = self.set_pass(refresh_token, pass_1, pass_2)
        self.assertEqual(200, rsp.status_code)

        auth_token, refresh_token = self.sign_in()
        rsp = self.set_pass(refresh_token, pass_2, pass_3)
        self.assertEqual(200, rsp.status_code)

        auth_token, refresh_token = self.sign_in()
        rsp = self.set_pass(refresh_token, pass_3, pass_4)
        self.assertEqual(200, rsp.status_code)

        auth_token, refresh_token = self.sign_in()
        rsp = self.set_pass(refresh_token, pass_4, pass_2)
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(ErrorCodes.ALREADY_USED_PASSWORD, rsp.json["code"])

        rsp = self.set_pass(refresh_token, pass_4, pass_1)
        self.assertEqual(200, rsp.status_code)

    def test_change_password(self):
        self.test_server.config.server.project.clients[0].authType = Client.AuthType.SFA
        # signing in 30 seconds earlier
        with freeze_time(datetime.utcnow() - relativedelta(seconds=30)):
            auth_token, refresh_token = self.sign_in()
        # initial set password
        rsp = set_auth_attributes(self.flask_client, auth_token, password=USER_PASSWORD)
        self.assertNotIn(SetAuthAttributesResponseObject.REFRESH_TOKEN, rsp.json)
        self.mocked_email_confirmation_adapter.send_password_changed_email.assert_not_called()

        # changing password
        new_password = "Some1234"
        rsp = self.set_pass(refresh_token, USER_PASSWORD, new_password)
        self.mocked_email_confirmation_adapter.send_password_changed_email.assert_called_once()
        new_refresh_token = rsp.json.get(SetAuthAttributesResponseObject.REFRESH_TOKEN)
        self.assertIsNotNone(new_refresh_token)

        # testing that no access with old auth token
        devices_resp = self.request_devices(auth_token)
        self.assertEqual(401, devices_resp.status_code)
        self.assertEqual(ErrorCodes.TOKEN_EXPIRED, devices_resp.json["code"])

        # confirming cannot refresh old token
        refresh_resp = self.refresh_token(refresh_token)
        self.assertEqual(401, refresh_resp.status_code)
        self.assertEqual(ErrorCodes.TOKEN_EXPIRED, refresh_resp.json["code"])

        # confirming can refresh new token from change password response
        refresh_resp = self.refresh_token(new_refresh_token)
        self.assertEqual(200, refresh_resp.status_code)

        # confirming cannot update password again with old token
        rsp = self.set_pass(refresh_token, new_password, USER_PASSWORD)
        self.assertEqual(401, rsp.status_code)

    def test_set_mfa_phone_number_not_sending_emails(self):
        auth_token, refresh_token = self.sign_in()
        set_auth_attributes(
            self.flask_client,
            refresh_token,
            password=USER_PASSWORD,
            token_type=TokenType.REFRESH.string_value,
            phone_number="+380500000000",
            confirmation_code="11111",
        )
        self.mocked_email_confirmation_adapter.send_mfa_phone_number_updated_email.assert_not_called()

    def test_only_change_mfa_phone_number_sending_emails(self):
        initial_phone_number = "+441347722095"

        auth_token, refresh_token = self.sign_in()
        set_auth_attributes(
            self.flask_client,
            refresh_token,
            token_type=TokenType.REFRESH.string_value,
            phone_number=initial_phone_number,
            confirmation_code="123456",
        )

        phone_confirmation_data = {
            ConfirmationRequestObject.EMAIL: USER_EMAIL,
            ConfirmationRequestObject.PHONE_NUMBER: initial_phone_number,
            ConfirmationRequestObject.CONFIRMATION_CODE: "11111",
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
        }
        phone_number_confirmation_response = self.flask_client.post(
            "/api/auth/v1beta/confirm", json=phone_confirmation_data, environ_base={}
        )
        self.assertEqual(200, phone_number_confirmation_response.status_code)
        self.mocked_email_confirmation_adapter.send_mfa_phone_number_updated_email.assert_not_called()

        # setting new phone number
        new_phone_number = "+380500000000"
        auth_token, refresh_token = self.sign_in()
        set_auth_attributes(
            self.flask_client,
            refresh_token,
            token_type=TokenType.REFRESH.string_value,
            phone_number=new_phone_number,
            confirmation_code="123456",
        )

        self.mocked_email_confirmation_adapter.send_mfa_phone_number_updated_email.assert_called_once()

    def test_invalid_header(self):

        with freeze_time(datetime.utcnow() - relativedelta(seconds=30)):
            auth_token, refresh_token = self.sign_in()

        auth_token = "Bearer" + auth_token
        devices_resp = self.request_devices(auth_token)
        self.assertEqual(401, devices_resp.status_code)
        self.assertEqual(ErrorCodes.WRONG_TOKEN, devices_resp.json["code"])
