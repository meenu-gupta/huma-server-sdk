from dataclasses import field

from sdk.common.usecase import response_object
from sdk.common.utils.convertible import convertibleclass, required_field, default_field


class SignUpResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        authToken: str = default_field()
        refreshToken: str = default_field()
        expiresIn: int = default_field()
        uid: str = default_field()

    def __init__(
        self,
        auth_token: str = None,
        refresh_token: str = None,
        expires_in: str = None,
        uid: str = None,
    ):
        super().__init__(
            value=self.Response(
                authToken=auth_token,
                refreshToken=refresh_token,
                expiresIn=expires_in,
                uid=uid,
            )
        )


class SuccessResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        ok: bool = field(default=True)

    def __init__(self, result=True):
        super().__init__(value=self.Response(ok=result))


class SendVerificationTokenResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        ok: bool = field(default=True)
        to: str = default_field()

    def __init__(self, result=True, to=None):
        super().__init__(value=self.Response(ok=result, to=to))


class RequestPasswordResetResponseObject(SuccessResponseObject):
    pass


class ConfirmationResponseObject(SuccessResponseObject):
    pass


class ResetPasswordResponseObject(SuccessResponseObject):
    pass


class SignInResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        authToken: str = default_field()
        refreshToken: str = default_field()
        expiresIn: str = default_field()
        uid: str = default_field()
        authTokenExpiresIn: int = default_field()

    def __init__(
        self,
        auth_token: str = None,
        refresh_token: str = None,
        expires_in: str = None,
        uid: str = None,
        auth_token_expires_in: str = None,
    ):
        super().__init__(
            value=self.Response(
                authToken=auth_token,
                refreshToken=refresh_token,
                expiresIn=expires_in,
                uid=uid,
                authTokenExpiresIn=auth_token_expires_in,
            )
        )


class RefreshTokenResponseObject(response_object.Response):
    REFRESH_TOKEN = "refreshToken"

    @convertibleclass
    class Response:
        authToken: str = default_field()
        expiresIn: str = default_field()
        refreshToken: str = default_field()
        refreshTokenExpiresIn: str = default_field()

    def __init__(
        self,
        auth_token: str,
        expires_in: int,
        refresh_token: str = None,
        refresh_token_expires_in: str = None,
    ):
        super().__init__(
            value=self.Response(
                authToken=auth_token,
                expiresIn=expires_in,
                refreshToken=refresh_token,
                refreshTokenExpiresIn=refresh_token_expires_in,
            )
        )


class AuthProfileResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        uid: str = default_field()

    def __init__(self, uid: str):
        super().__init__(value=self.Response(uid=uid))


class SetAuthAttributesResponseObject(response_object.Response):
    UID = "uid"
    REFRESH_TOKEN = "refreshToken"

    @convertibleclass
    class Response:
        uid: str = default_field()
        refreshToken: str = default_field()

    def __init__(self, uid: str, refresh_token: str = None):
        super().__init__(value=self.Response(uid=uid, refreshToken=refresh_token))


class CheckAuthAttributesResponseObject(response_object.Response):
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"
    PASSWORD_SET = "password_set"
    EMAIL_VERIFIED = "email_verified"
    PHONE_NUMBER_VERIFIED = "phone_number_verified"
    ELIGIBLE_FOR_MFA = "eligible_for_mfa"
    MFA_ENABLED = "mfa_enabled"

    @convertibleclass
    class Response:
        phoneNumber: str = default_field()
        email: str = default_field()
        passwordSet: bool = default_field()
        emailVerified: bool = default_field()
        phoneNumberVerified: bool = default_field()
        eligibleForMFA: bool = default_field()
        mfaEnabled: bool = default_field()

    def __init__(
        self,
        email: str,
        eligible_for_mfa: bool,
        phone_number: str = None,
        password_set: bool = None,
        email_verified: bool = None,
        phone_number_verified: bool = None,
        mfa_enabled: bool = None,
    ):
        super().__init__(
            value=self.Response(
                phoneNumber=phone_number,
                email=email,
                passwordSet=password_set,
                emailVerified=email_verified,
                phoneNumberVerified=phone_number_verified,
                eligibleForMFA=eligible_for_mfa,
                mfaEnabled=mfa_enabled,
            )
        )


class RetrieveDeepLinkAppleAppResponseObject(response_object.Response):
    def __init__(self, rsp: dict):
        super().__init__(value=rsp)


class GenerateAuthKeysResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        authId: str = required_field()
        authKey: str = required_field()

    def __init__(self, auth_id: str, auth_key: str):
        super().__init__(value=self.Response(authId=auth_id, authKey=auth_key))
