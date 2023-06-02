from unittest.mock import MagicMock

from sdk.auth.enums import Method
from sdk.auth.model.auth_user import AuthUser, AuthIdentifier, AuthIdentifierType
from sdk.auth.use_case.auth_request_objects import (
    SendVerificationTokenRequestObject,
    SignInRequestObject,
    ConfirmationRequestObject,
    SetAuthAttributesRequestObject,
    RefreshTokenRequestObject,
    CheckAuthAttributesRequestObject,
    SignOutRequestObjectV1,
)
from sdk.common.exceptions.exceptions import UnauthorizedException
from sdk.common.utils.validators import remove_none_values

USER_EMAIL = "usertest@test.com"
USER_PHONE_NUMBER = "+441347722095"
USER_PASSWORD = "Test123456"
USER_HASHED_PASSWORD_VALUE = (
    "$2b$12$lIrfiYZjjapbrQ9gkhphdecVgAI79SXwCTTgYkpbg8T3kIrRH9bGm"
)
USER_ID = "5e8f0c74b50aa9656c34789a"
CONFIRMATION_CODE = "123456"
NOT_EXISTING_PHONE_NUMBER = "+441347722096"
NOT_EXISTING_EMAIL = "new+user@test.com"
TEST_USER_AGENT = "chrome"
REFRESH_TOKEN = "refresh_token"
ACCESS_TOKEN = "access_token"

TEST_CLIENT_ID = "ctest1"
CLIENT_ID_3 = "c3"
PROJECT_ID = "ptest1"
TEST_CLIENT_ID_MINIMUM_VERSION = "1.17.1"


def auth_user():
    return AuthUser(id=USER_ID, status=AuthUser.Status.NORMAL, email=USER_EMAIL)


def filled_auth_user(
    identifier_verified=True,
    mfa_phone_number=USER_PHONE_NUMBER,
    phone_number=USER_PHONE_NUMBER,
):
    identifier = AuthIdentifier(
        type=AuthIdentifierType.PHONE_NUMBER,
        value=mfa_phone_number,
        verified=identifier_verified,
    )
    return AuthUser(
        id=USER_ID,
        status=AuthUser.Status.NORMAL,
        email=USER_EMAIL,
        hashedPassword="123",
        phoneNumber=phone_number,
        emailVerified=True,
        mfaIdentifiers=[identifier],
    )


def hashed_password_mock(password):
    return USER_HASHED_PASSWORD_VALUE


def get_auth_repo_with_user(user: AuthUser):
    def get_user_mocked(phone_number: str = None, email: str = None, uid: str = None):
        user_phone_number_identifier = user.get_mfa_identifier(
            AuthIdentifierType.PHONE_NUMBER
        )
        user_phone_number = (
            user_phone_number_identifier.value if user_phone_number_identifier else None
        )
        if phone_number == user_phone_number or email == user.email or uid == user.id:
            return user
        raise UnauthorizedException

    auth_repo = MagicMock()
    auth_repo.get_user.side_effect = get_user_mocked
    return auth_repo


def email_password_sign_in_request(flask_client, email: str, password: str):
    sign_in_data = {
        SignInRequestObject.METHOD: Method.EMAIL_PASSWORD,
        SignInRequestObject.CLIENT_ID: "c3",
        SignInRequestObject.PROJECT_ID: "ptest1",
        SignInRequestObject.EMAIL: email,
        SignInRequestObject.PASSWORD: password,
    }
    return flask_client.post("/api/auth/v1beta/signin", json=sign_in_data)


def email_sign_in_request(flask_client, email: str, code: str):
    sign_in_data = {
        SignInRequestObject.METHOD: Method.EMAIL,
        SignInRequestObject.CLIENT_ID: "c3",
        SignInRequestObject.PROJECT_ID: "ptest1",
        SignInRequestObject.EMAIL: email,
        SignInRequestObject.CONFIRMATION_CODE: code,
    }
    return flask_client.post("/api/auth/v1beta/signin", json=sign_in_data)


def phone_number_sign_in_request(flask_client, phone_number: str, code: str):
    sign_in_data = {
        SignInRequestObject.METHOD: Method.PHONE_NUMBER,
        SignInRequestObject.CLIENT_ID: "c3",
        SignInRequestObject.PROJECT_ID: "ptest1",
        SignInRequestObject.PHONE_NUMBER: phone_number,
        SignInRequestObject.CONFIRMATION_CODE: code,
    }
    return flask_client.post("/api/auth/v1beta/signin", json=sign_in_data)


def tfa_sign_in_request(flask_client, refresh_token: str, code: str):
    sign_in_data = {
        SignInRequestObject.METHOD: Method.TWO_FACTOR_AUTH,
        SignInRequestObject.CLIENT_ID: "c3",
        SignInRequestObject.PROJECT_ID: "ptest1",
        SignInRequestObject.REFRESH_TOKEN: refresh_token,
        SignInRequestObject.CONFIRMATION_CODE: code,
    }
    return flask_client.post("/api/auth/v1beta/signin", json=sign_in_data)


def send_verification_token(
    flask_client, method, email=None, phone_number=None, client_id=None
):
    data = {
        SendVerificationTokenRequestObject.CLIENT_ID: client_id or "ctest1",
        SendVerificationTokenRequestObject.PROJECT_ID: "ptest1",
        SendVerificationTokenRequestObject.METHOD: method,
        SendVerificationTokenRequestObject.EMAIL: email,
        SendVerificationTokenRequestObject.PHONE_NUMBER: phone_number,
    }
    rsp = flask_client.post(
        "/api/auth/v1beta/sendverificationtoken", json=remove_none_values(data)
    )
    return rsp


def send_phone_number_confirmation_request(flask_client, phone_number, email):
    data = {
        ConfirmationRequestObject.PHONE_NUMBER: phone_number,
        ConfirmationRequestObject.CONFIRMATION_CODE: CONFIRMATION_CODE,
        ConfirmationRequestObject.EMAIL: email,
        ConfirmationRequestObject.CONFIRMATION_TYPE: ConfirmationRequestObject.ConfirmationType.PHONE_NUMBER.value,
    }
    return flask_client.post("/api/auth/v1beta/confirm", json=data)


def request_auth_attributes(flask_client, auth_token):
    return flask_client.post(
        "/api/auth/v1beta/check-auth-attributes",
        json={
            CheckAuthAttributesRequestObject.AUTH_TOKEN: auth_token,
            CheckAuthAttributesRequestObject.CLIENT_ID: TEST_CLIENT_ID,
            CheckAuthAttributesRequestObject.PROJECT_ID: PROJECT_ID,
        },
    )


def set_auth_attributes(
    flask_client,
    auth_token,
    email=None,
    password=None,
    phone_number=None,
    token_type=None,
    old_password=None,
    confirmation_code=None,
):
    data = {
        SetAuthAttributesRequestObject.AUTH_TOKEN: auth_token,
        SetAuthAttributesRequestObject.EMAIL: email,
        SetAuthAttributesRequestObject.PASSWORD: password,
        SetAuthAttributesRequestObject.PHONE_NUMBER: phone_number,
        SetAuthAttributesRequestObject.CLIENT_ID: TEST_CLIENT_ID,
        SetAuthAttributesRequestObject.PROJECT_ID: PROJECT_ID,
        SetAuthAttributesRequestObject.TOKEN_TYPE: token_type,
        SetAuthAttributesRequestObject.OLD_PASSWORD: old_password,
        SetAuthAttributesRequestObject.CONFIRMATION_CODE: confirmation_code,
    }
    return flask_client.post(
        "/api/auth/v1beta/set-auth-attributes", json=remove_none_values(data)
    )


def get_auth_token(flask_client, refresh_token):
    rsp = flask_client.post(
        "/api/auth/v1beta/refreshtoken",
        json={RefreshTokenRequestObject.REFRESH_TOKEN: refresh_token},
    )
    return rsp.json["authToken"]


def sample_sign_out_req_obj_v1():
    return {
        SignOutRequestObjectV1.USER_ID: USER_ID,
        SignOutRequestObjectV1.REFRESH_TOKEN: "refresh_token",
        SignOutRequestObjectV1.DEVICE_TOKEN: "device_token",
        SignOutRequestObjectV1.DEVICE_PUSH_ID: "push_id",
        SignOutRequestObjectV1.DEVICE_AGENT: "agent",
    }
