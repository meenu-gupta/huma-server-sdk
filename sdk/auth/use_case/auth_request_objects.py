import datetime
from dataclasses import field

import pytz
from flask import g

from sdk.auth.enums import Method, SendVerificationTokenMethod, AuthStage
from sdk.auth.model.auth_user import AuthKey, AuthUser
from sdk.auth.model.session import DeviceSession, DeviceSessionV1
from sdk.auth.validators import validate_project_and_client_id
from sdk.common.adapter.token_adapter import TokenType
from sdk.common.localization.utils import Language
from sdk.common.usecase import request_object
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    ConvertibleClassValidationError,
    required_field,
    default_field,
)
from sdk.common.utils.hash_utils import hash_new_password
from sdk.common.utils.validators import (
    validate_email,
    must_be_present,
    validate_timezone,
    password_validator,
    replace_spaces,
    not_empty,
    incorrect_language_to_default,
    must_be_at_least_one_of,
    must_be_only_one_of,
    default_phone_number_meta,
    validate_object_id,
    remove_none_values,
    must_not_be_present,
)


def inject_language(body: dict):
    """Updates language from flask.g if no language in body"""

    language_key = "language"
    try:
        if language_key in body or language_key not in g:
            return

        if language := getattr(g, language_key):
            body.update({language_key: language})

    except RuntimeError:
        return


@convertibleclass
class BaseAuthRequestObject(request_object.RequestObject):
    CLIENT_ID = "clientId"
    PROJECT_ID = "projectId"
    LANGUAGE = "language"

    language: str = field(
        default=Language.EN, metadata=meta(value_to_field=incorrect_language_to_default)
    )
    clientId: str = required_field(metadata=meta(not_empty))
    projectId: str = required_field(metadata=meta(not_empty))

    @classmethod
    def validate(cls, request):
        validate_project_and_client_id(request.clientId, request.projectId)


@convertibleclass
class SignUpRequestObject(BaseAuthRequestObject):
    EMAIL = "email"
    PASSWORD = "password"
    USER_ATTRIBUTES = "userAttributes"
    METHOD = "method"
    PHONE_NUMBER = "phoneNumber"
    VALIDATION_DATA = "validationData"
    DISPLAY_NAME = "displayName"
    TIMEZONE = "timezone"

    method: Method = required_field()
    email: str = default_field(
        metadata=meta(validate_email, value_to_field=replace_spaces),
    )
    phoneNumber: str = default_field(metadata=default_phone_number_meta())
    password: str = default_field(metadata=meta(password_validator))
    displayName: str = default_field()
    validationData: dict = default_field()
    userAttributes: dict = default_field()
    timezone: str = field(default="UTC", metadata=meta(validate_timezone))

    @classmethod
    def validate(cls, request):
        super().validate(request)
        if request.method == Method.PHONE_NUMBER:
            must_be_present(phoneNumber=request.phoneNumber)
        elif request.method == Method.EMAIL:
            must_be_present(email=request.email)
        elif request.method == Method.EMAIL_PASSWORD:
            must_be_present(email=request.email, password=request.password)
        elif request.method == Method.TWO_FACTOR_AUTH:
            must_be_present(
                email=request.email,
                password=request.password,
            )

    def to_auth_user(self) -> AuthUser:
        now = datetime.datetime.utcnow()
        user_data = {
            AuthUser.STATUS: AuthUser.Status.NORMAL,
            AuthUser.EMAIL: self.email,
            AuthUser.PHONE_NUMBER: self.phoneNumber,
            AuthUser.DISPLAY_NAME: self.displayName,
            AuthUser.USER_ATTRIBUTES: self.userAttributes,
            AuthUser.CREATE_DATE_TIME: now,
            AuthUser.UPDATE_DATE_TIME: now,
        }
        if self.password:
            hashed_password = hash_new_password(self.password)
            user_data.update(
                {
                    AuthUser.HASHED_PASSWORD: hashed_password,
                    AuthUser.PASSWORD_CREATE_DATE_TIME: now,
                    AuthUser.PASSWORD_UPDATE_DATE_TIME: now,
                }
            )
        return AuthUser.from_dict(remove_none_values(user_data))


@convertibleclass
class SendVerificationTokenRequestObject(BaseAuthRequestObject):
    METHOD = "method"
    EMAIL = "email"
    PHONE_NUMBER = "phoneNumber"
    REFRESH_TOKEN = "refreshToken"

    method: SendVerificationTokenMethod = required_field()
    email: str = default_field(
        metadata=meta(validate_email, value_to_field=replace_spaces),
    )
    phoneNumber: str = default_field(metadata=default_phone_number_meta())
    language: str = field(default=Language.EN)
    refreshToken: str = default_field(metadata=meta(not_empty))

    @classmethod
    def validate(cls, request):
        super().validate(request)
        if request.method == SendVerificationTokenMethod.PHONE_NUMBER:
            must_be_present(phoneNumber=request.phoneNumber)
        elif request.method == SendVerificationTokenMethod.TWO_FACTOR_AUTH:
            must_be_present(refreshToken=request.refreshToken)
        else:
            must_be_present(email=request.email)


@convertibleclass
class RequestPasswordResetRequestObject(BaseAuthRequestObject):
    EMAIL = "email"

    email: str = required_field(
        metadata=meta(validate_email, value_to_field=replace_spaces),
    )


@convertibleclass
class ResetPasswordRequestObject(request_object.RequestObject):
    EMAIL = "email"
    CODE = "code"
    NEW_PASSWORD = "newPassword"

    email: str = required_field(
        metadata=meta(validate_email, value_to_field=replace_spaces),
    )
    code: str = required_field(metadata=meta(not_empty))
    newPassword: str = required_field(metadata=meta(password_validator))


@convertibleclass
class SignInRequestObject(BaseAuthRequestObject):
    METHOD = "method"
    PHONE_NUMBER = "phoneNumber"
    EMAIL = "email"
    CONFIRMATION_CODE = "confirmationCode"
    REFRESH_TOKEN = "refreshToken"
    PASSWORD = "password"
    DEVICE_AGENT = "deviceAgent"

    method: Method = required_field()
    email: str = default_field(
        metadata=meta(validate_email, value_to_field=replace_spaces),
    )
    refreshToken: str = default_field(metadata=meta(not_empty))
    phoneNumber: str = default_field(metadata=default_phone_number_meta())
    confirmationCode: str = default_field(metadata=meta(not_empty))
    password: str = default_field(metadata=meta(not_empty))
    deviceAgent: str = default_field()
    authStage: AuthStage = default_field()

    @classmethod
    def validate(cls, request):
        super().validate(request)
        if request.method == Method.PHONE_NUMBER:
            must_be_present(
                phoneNumber=request.phoneNumber,
                confirmationCode=request.confirmationCode,
            )
        elif request.method == Method.EMAIL:
            must_be_present(
                email=request.email, confirmationCode=request.confirmationCode
            )
        elif request.method == Method.EMAIL_PASSWORD:
            must_be_present(email=request.email, password=request.password)

    def post_init(self):
        if self.method is Method.TWO_FACTOR_AUTH:
            if self.email and self.password:
                self.authStage = AuthStage.FIRST
            elif self.refreshToken and self.confirmationCode:
                self.authStage = AuthStage.SECOND
            else:
                raise ConvertibleClassValidationError(
                    'At least one of "email and password", "refreshToken and confirmationCode",'
                    "should be present"
                )


@convertibleclass
class SignInRequestObjectV1(SignInRequestObject):
    def post_init(self):
        must_not_be_present(authStage=self.authStage)
        if self.method is not Method.TWO_FACTOR_AUTH:
            return

        if self.refreshToken:
            if self.email and self.password:
                self.authStage = AuthStage.REMEMBER_ME
            elif self.confirmationCode:
                self.authStage = AuthStage.SECOND
            else:
                raise ConvertibleClassValidationError(
                    'At least one of "email and password" or "confirmationCode",'
                    "should be present when refreshToken is present"
                )
        elif self.email and self.password:
            self.authStage = AuthStage.FIRST
        else:
            raise ConvertibleClassValidationError(
                'At least one of "email and password", "refreshToken",'
                "should be present"
            )


@convertibleclass
class SignOutRequestObject(request_object.RequestObject, DeviceSession):
    pass


@convertibleclass
class SignOutRequestObjectV1(request_object.RequestObject, DeviceSessionV1):
    DEVICE_PUSH_ID = "devicePushId"
    DEVICE_TOKEN = "deviceToken"
    VOIP_DEVICE_PUSH_ID = "voipDevicePushId"

    devicePushId: str = default_field(metadata=meta(not_empty))
    deviceToken: str = default_field(metadata=meta(not_empty))
    voipDevicePushId: str = default_field(metadata=meta(not_empty))

    @classmethod
    def validate(cls, request):
        must_be_present(refreshToken=request.refreshToken, userId=request.userId)


@convertibleclass
class RefreshTokenRequestObject(request_object.RequestObject):
    REFRESH_TOKEN = "refreshToken"
    PASSWORD = "password"
    DEVICE_AGENT = "deviceAgent"
    EMAIL = "email"

    refreshToken: str = required_field(metadata=meta(not_empty))
    password: str = default_field(metadata=meta(password_validator))
    email: str = default_field(metadata=meta(validate_email))
    deviceAgent: str = default_field()

    @classmethod
    def validate(cls, request):
        if request.password or request.email:
            must_be_present(password=request.password, email=request.email)


@convertibleclass
class RefreshTokenRequestObjectV1(request_object.RequestObject):
    REFRESH_TOKEN = "refreshToken"
    PASSWORD = "password"
    DEVICE_AGENT = "deviceAgent"
    EMAIL = "email"
    DEVICE_TOKEN = "deviceToken"

    refreshToken: str = required_field(metadata=meta(not_empty))
    password: str = default_field(metadata=meta(password_validator))
    email: str = default_field(metadata=meta(validate_email))
    deviceAgent: str = default_field()
    deviceToken: str = default_field()

    @classmethod
    def validate(cls, request):
        if request.email:
            must_be_only_one_of(
                password=request.password, deviceToken=request.deviceToken
            )


@convertibleclass
class AuthProfileRequestObject(request_object.RequestObject):
    AUTH_TOKEN = "authToken"

    authToken: str = required_field(metadata=meta(not_empty))


@convertibleclass
class ConfirmationRequestObject(request_object.RequestObject):
    EMAIL = "email"
    PHONE_NUMBER = "phoneNumber"
    CONFIRMATION_CODE = "confirmationCode"
    DEVICE_AGENT = "deviceAgent"
    CLIENT_ID = "clientId"
    PROJECT_ID = "projectId"

    email: str = required_field(
        metadata=meta(validate_email, value_to_field=replace_spaces),
    )
    phoneNumber: str = default_field(metadata=default_phone_number_meta())
    confirmationCode: str = required_field(metadata=meta(not_empty))
    clientId: str = required_field(metadata=meta(not_empty))
    projectId: str = required_field(metadata=meta(not_empty))
    deviceAgent: str = default_field()


@convertibleclass
class SetAuthAttributesRequestObject(BaseAuthRequestObject):
    AUTH_TOKEN = "authToken"
    TOKEN_TYPE = "tokenType"
    CONFIRMATION_TOKEN = "confirmationToken"
    EMAIL = "email"
    PHONE_NUMBER = "phoneNumber"
    PASSWORD = "password"
    MFA_ENABLED = "mfaEnabled"
    OLD_PASSWORD = "oldPassword"
    CONFIRMATION_CODE = "confirmationCode"
    DEVICE_TOKEN = "deviceToken"

    email: str = default_field(metadata=meta(validate_email))
    phoneNumber: str = default_field(metadata=default_phone_number_meta())
    password: str = default_field(metadata=meta(password_validator))
    authToken: str = default_field(metadata=meta(not_empty))
    tokenType: TokenType = field(default=TokenType.ACCESS)
    confirmationToken: str = default_field(metadata=meta(not_empty))
    mfaEnabled: bool = default_field()
    oldPassword: str = default_field(metadata=meta(password_validator))
    confirmationCode: str = default_field(metadata=meta(not_empty))
    deviceToken: str = default_field()

    @classmethod
    def validate(cls, request):
        super().validate(request)
        must_be_at_least_one_of(
            email=request.email,
            phoneNumber=request.phoneNumber,
            password=request.password,
            mfaEnabled=request.mfaEnabled,
            deviceToken=request.deviceToken,
        )
        must_be_present(authToken=request.authToken)

        if request.oldPassword:
            must_be_present(authToken=request.password)
            if not request.tokenType == TokenType.REFRESH:
                raise ConvertibleClassValidationError("Refresh token must be provided")


@convertibleclass
class CheckAuthAttributesRequestObject:
    AUTH_TOKEN = "authToken"
    TOKEN_TYPE = "tokenType"
    EMAIL = "email"
    PHONE_NUMBER = "phoneNumber"
    PROJECT_ID = "projectId"
    CLIENT_ID = "clientId"

    authToken: str = default_field(metadata=meta(not_empty))
    tokenType: TokenType = field(default=TokenType.ACCESS)
    email: str = default_field(metadata=meta(validate_email))
    phoneNumber: str = default_field(metadata=default_phone_number_meta())
    clientId: str = required_field(metadata=meta(not_empty))
    projectId: str = required_field(metadata=meta(not_empty))

    @classmethod
    def validate(cls, request):
        must_be_only_one_of(
            authToken=request.authToken,
            email=request.email,
            phoneNumber=request.phoneNumber,
        )


@convertibleclass
class DeleteUserRequestObject:
    USER_ID = "userId"

    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class GenerateAuthKeysRequestObject:
    USER_ID = "userId"

    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class CreateServiceAccountRequestObject:
    SERVICE_ACCOUNT_NAME = "serviceAccountName"
    AUTH_TYPE = "authType"
    VALIDATION_DATA = "validationData"
    ROLE_ID = "roleId"
    RESOURCE_ID = "resourceId"
    TIMEZONE = "timezone"

    serviceAccountName: str = required_field()
    authType: AuthKey.AuthType = field(default=AuthKey.AuthType.HAWK)
    validationData: dict = required_field()
    roleId: str = required_field()
    resourceId: str = required_field()
    timezone: str = field(default=pytz.utc.zone, metadata=meta(validate_timezone))

    @classmethod
    def validate(cls, instance):
        email = instance.get_email()
        if not validate_email(email):
            raise ConvertibleClassValidationError(f"The email {email} is invalid")

    def get_email(self):
        return f"{self.serviceAccountName}@serviceaccount.huma.com"
