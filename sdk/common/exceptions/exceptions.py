import logging
from typing import Optional


class ErrorCodes:
    WRONG_TOKEN = 10002
    INVALID_PROJECT_ID = 100001
    INVALID_CLIENT_ID = 100002
    INVALID_REQUEST = 100003
    FORBIDDEN_ID = 100004
    NOT_REGISTERED_CLASS = 100005
    UNAUTHORIZED = 100006
    BUCKET_NOT_ALLOWED = 100007
    BUCKET_OR_FILE_DOES_NOT_EXIST = 100008
    RATE_LIMIT_EXCEEDED = 100009
    UPDATE_REQUIRED = 100426
    ENCRYPTION_FAILED = 100427
    FILE_CACHE_LOOKUP_FAILED = 100428

    # auth
    TOKEN_EXPIRED = 10001
    DUPLICATED_USER_ID = 100010
    INVALID_CONFIRMATION_TOKEN = 100011
    INVALID_USERNAME_OR_PASSWORD = 100012
    USERNAME_UNCONFIRMED = 100013
    USER_ALREADY_SIGNED_OUT = 100014
    EMAIL_NOT_VERIFIED = 100015
    INVALID_EMAIL_CONFIRMATION_CODE = 100016
    SESSION_TIMEOUT = 100017
    PASSWORD_NOT_SET = 100018
    PHONE_NUMBER_NOT_SET = 100019
    INVALID_VERIFICATION_CODE = 100020
    TOKEN_NOT_VALID_FOR_MULTI_FACTOR_AUTH = 100021
    EMAIL_NOT_SET = 100022
    TOKEN_PROVIDER_INVALID = 100023
    EMAIL_ALREADY_SET = 100024
    PHONE_NUMBER_ALREADY_SET = 100025
    PASSWORD_ALREADY_SET = 100026
    PHONE_NUMBER_NOT_VERIFIED = 100027
    DUPLICATED_PHONE_NUMBER = 100028
    SECOND_FACTOR_AUTH_REQUIRED = 100029
    PHONE_NUMBER_ALREADY_VERIFIED = 100030
    EMAIL_NUMBER_ALREADY_VERIFIED = 100031
    PASSWORD_EXPIRED = 100032
    INVITATION_CODE_EXPIRED = 100033
    INVALID_ROLE_ID = 100034
    ONFIDO_SDK_TOKEN_GENERATION_FAILED = 100035
    BUNDLE_ID_MISSING = 100036
    ONFIDO_CREATE_APPLICANT_FAILED = 100037
    CONSENT_NOT_AGREED = 100038
    ONFIDO_CREATE_CHECK_FAILED = 100039
    ID_VERIFICATION_IN_PROGRESS = 100040
    ID_VERIFICATION_NEEDED = 100041
    ID_VERIFICATION_FAILED = 100042
    MFA_REQUIRED = 100043
    INVALID_MODULE_CONFIG_BODY = 100044
    INVALID_PHONE_NUMBER = 100045
    ROLE_DOES_NOT_EXIST = 100046
    USER_WITHOUT_ROLES = 100047
    INVALID_PASSWORD = 100048
    SESSION_DOES_NOT_EXIST = 100049
    DATA_VALIDATION_ERROR = 100050
    ALREADY_USED_PASSWORD = 100051
    CONFIRMATION_CODE_IS_MISSING = 100052
    USER_ALREADY_ACTIVE = 100053
    USER_ALREADY_OFFBOARDED = 100054
    MODULE_RAG_CONFIG_EXISTS = 100055
    INVALID_SHORT_INVITATION_CODE = 100056

    # Auto complete module
    INVALID_AUTOCOMPLETE_ENDPOINT = 110001

    DUPLICATE_PRIMITIVE = 120001

    INTERNAL_SERVER_ERROR = 13001


class DetailedException(Exception):
    status_code = 400

    def __init__(
        self,
        code,
        debug_message,
        status_code=None,
        payload=None,
        log_level: int = logging.ERROR,
    ):
        Exception.__init__(self)
        self.code = code
        self.debug_message = debug_message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        self.log_level = log_level
        self.args = (debug_message,)

    def to_dict(self):
        return {
            **(self.payload or {}),
            "code": self.code,
            "message": self.debug_message,
        }

    def __str__(self):
        return self.debug_message or str(self.to_dict())


class InvalidRequestException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=message or "Invalid Request",
            status_code=400,
        )


class UnauthorizedException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.UNAUTHORIZED,
            debug_message=message or "Unauthorized User",
            status_code=401,
        )


class InvalidUsernameOrPasswordException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_USERNAME_OR_PASSWORD,
            debug_message=message or "Invalid Username or Password",
            status_code=403,
        )


class UsernameUnconfirmedException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.USERNAME_UNCONFIRMED,
            debug_message="Username not confirmed",
            status_code=400,
        )


class ClassNotRegisteredException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.NOT_REGISTERED_CLASS,
            debug_message="Class not registered",
            status_code=400,
        )


class UserAlreadySignedOutException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.USER_ALREADY_SIGNED_OUT,
            debug_message="User is already signed out",
            status_code=403,
        )


class DeviceSessionDoesNotExistException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.SESSION_DOES_NOT_EXIST,
            debug_message="Device session doesn't exist",
            status_code=400,
        )


class PermissionDenied(DetailedException):
    def __init__(self, msg=None):
        super().__init__(
            code=ErrorCodes.FORBIDDEN_ID,
            debug_message=msg or "Action not allowed for current user.",
            status_code=403,
        )


class ClientPermissionDenied(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.INVALID_CLIENT_ID,
            debug_message="Action not allowed using this client.",
            status_code=403,
        )


class BucketNotAllowedException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.BUCKET_NOT_ALLOWED,
            debug_message=message or "Bucket not allowed",
            status_code=400,
        )


class BucketFileDoesNotExist(DetailedException):
    def __init__(self, message=None):
        super(BucketFileDoesNotExist, self).__init__(
            code=ErrorCodes.BUCKET_OR_FILE_DOES_NOT_EXIST,
            debug_message=message or "Bucket or File doesn't exist",
            status_code=400,
        )


class EmailNotVerifiedException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.EMAIL_NOT_VERIFIED,
            debug_message="Email not verified",
            status_code=400,
        )


class InvalidEmailConfirmationCodeException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_EMAIL_CONFIRMATION_CODE,
            debug_message=message or "Invalid email confirmation code",
            status_code=401,
        )


class ClientUpdateRequiredException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.UPDATE_REQUIRED,
            debug_message=message or "Client app update required",
            status_code=426,
        )


class SessionTimeoutException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.SESSION_TIMEOUT,
            debug_message=message or "Session timeout",
            status_code=401,
        )


class PasswordNotSetException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.PASSWORD_NOT_SET,
            debug_message=message or "Password not set",
            status_code=401,
        )


class EmailNotSetException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.EMAIL_NOT_SET,
            debug_message=message or "Email not set",
            status_code=401,
        )


class PhoneNumberNotSetException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.PHONE_NUMBER_NOT_SET,
            debug_message="Phone number not set",
            status_code=400,
        )


class ConfirmationCodeIsMissing(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.CONFIRMATION_CODE_IS_MISSING,
            debug_message="Confirmation code is missing",
            status_code=400,
        )


class PhoneNumberNotVerifiedException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.PHONE_NUMBER_NOT_VERIFIED,
            debug_message="Phone number not verified",
            status_code=401,
        )


class InvalidVerificationCodeException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_VERIFICATION_CODE,
            debug_message=message or "Invalid verification code",
            status_code=400,
        )


class InvalidConfirmationTokenException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_CONFIRMATION_TOKEN,
            debug_message=message or "Invalid confirmation token",
            status_code=400,
        )


class AccessTokenNotValidForMultiFactorAuthException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.TOKEN_NOT_VALID_FOR_MULTI_FACTOR_AUTH,
            debug_message="Access token is not valid for Multi-Factor Auth",
            status_code=400,
        )


class InvalidTokenProviderException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.TOKEN_PROVIDER_INVALID,
            debug_message=message or "Invalid token provider",
            status_code=400,
        )


class EmailAlreadySetException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.EMAIL_ALREADY_SET,
            debug_message="Email already set",
            status_code=400,
        )


class PhoneNumberAlreadySetException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.PHONE_NUMBER_ALREADY_SET,
            debug_message="Phone number already set",
            status_code=400,
        )


class EmailAlreadyVerifiedException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.EMAIL_NUMBER_ALREADY_VERIFIED,
            debug_message="Email already verified",
            status_code=400,
        )


class PhoneNumberAlreadyVerifiedException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.PHONE_NUMBER_ALREADY_VERIFIED,
            debug_message="Phone number already verified",
            status_code=400,
        )


class PasswordAlreadySetException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.PASSWORD_ALREADY_SET,
            debug_message="Password already set",
            status_code=400,
        )


class WrongTokenException(DetailedException):
    def __init__(self, message: Optional[str] = None):
        super().__init__(
            code=ErrorCodes.WRONG_TOKEN,
            debug_message=message or "Wrong Token",
            status_code=401,
            log_level=logging.DEBUG,
        )


class DuplicatedPhoneNumberException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.DUPLICATED_PHONE_NUMBER,
            debug_message="Phone number already exists in system",
            status_code=400,
        )


class UserAlreadyExistsException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.DUPLICATED_USER_ID,
            debug_message="User already exists",
            status_code=400,
        )


class SecondFactorAuthRequired(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.SECOND_FACTOR_AUTH_REQUIRED,
            debug_message="Second factor auth required",
            status_code=400,
        )


class PasswordExpiredException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.PASSWORD_EXPIRED,
            debug_message=message or "Password expired",
            status_code=403,
        )


class OnfidoSdkTokenGenerationException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.ONFIDO_SDK_TOKEN_GENERATION_FAILED,
            debug_message=message or "Onfido SDK Token Generation Failed",
            status_code=400,
        )


class OnfidoCreateApplicantException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.ONFIDO_CREATE_APPLICANT_FAILED,
            debug_message=message or "Onfido Creating Applicant Failed",
            status_code=400,
        )


class InvalidRoleException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_ROLE_ID,
            debug_message=message or "Invalid role provided",
            status_code=400,
        )


class RoleDoesNotExist(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.ROLE_DOES_NOT_EXIST,
            debug_message=message
            or "Role Doesn't exist. Please click refresh to see the latest updates in roles.",
            status_code=404,
        )


class BundleIdMissingException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.BUNDLE_ID_MISSING,
            debug_message="Bundle Id is missing in the request header",
            status_code=400,
        )


class InvitationExpiredException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVITATION_CODE_EXPIRED,
            debug_message=message or "Invitation expired",
            status_code=401,
        )


class InvalidShortInvitationCodeException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_SHORT_INVITATION_CODE,
            debug_message=message or "Invalid short invitation code",
            status_code=401,
        )


class MFARequiredException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.MFA_REQUIRED,
            debug_message=message or "MFA is required",
            status_code=403,
        )


class OnfidoCreateCheckException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.ONFIDO_CREATE_CHECK_FAILED,
            debug_message=message or "Onfido Creating Check Failed",
        )


class ConsentNotAgreedException(DetailedException):
    def __init__(self):
        super().__init__(
            code=ErrorCodes.CONSENT_NOT_AGREED,
            debug_message=f"Must agree Consent Agreement",
            status_code=400,
        )


class IdVerificationNeededException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.ID_VERIFICATION_NEEDED,
            debug_message=message or "ID verification needed",
            status_code=428,
        )


class IdVerificationInProgressException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.ID_VERIFICATION_IN_PROGRESS,
            debug_message=message or "ID verification in progress",
            status_code=428,
        )


class IdVerificationFailedException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.ID_VERIFICATION_FAILED,
            debug_message=message or "ID verification failed",
            status_code=428,
        )


class InvalidPhoneNumberException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_PHONE_NUMBER,
            debug_message=message or "Invalid phone number",
            status_code=400,
        )


class UserWithoutAnyRoleException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.USER_WITHOUT_ROLES,
            debug_message=message
            or "Your account does not exist or have the right permissions. Please contact your Admin to be invited again.",
            status_code=400,
        )


class RateLimitException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.RATE_LIMIT_EXCEEDED,
            debug_message=message or "Amount of tries exceeded the limit",
            status_code=429,
        )


class DuplicatePrimitiveException(DetailedException):
    def __init__(self, name=None, message=None):
        super().__init__(
            code=ErrorCodes.DUPLICATE_PRIMITIVE,
            debug_message=message or f"Duplicate submission for: {name}",
            status_code=422,
        )


class FileNotRegisteredInCache(DetailedException):
    def __init__(self, name=None, message=None):
        super().__init__(
            code=ErrorCodes.FILE_CACHE_LOOKUP_FAILED,
            debug_message=message or f"File is not registred in cache: {name}",
            status_code=400,
        )


class ObjectDoesNotExist(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=message or "Object does not exist",
            status_code=404,
        )


class InvalidPasswordException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_PASSWORD,
            debug_message=message or "Invalid Password",
            status_code=403,
        )


class TokenExpiredException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.TOKEN_EXPIRED,
            debug_message=message or "Token Expired",
            status_code=401,
            log_level=logging.DEBUG,
        )


class AlreadyUsedPasswordException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.ALREADY_USED_PASSWORD,
            debug_message=message or "Password was already used earlier",
            status_code=400,
        )


class InvalidModuleConfigBody(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_MODULE_CONFIG_BODY,
            debug_message=message or "Invalid module config body",
            status_code=400,
        )


class PageNotFoundException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=message or "Page Not Found",
            status_code=404,
        )


class FileNotFoundException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.BUCKET_OR_FILE_DOES_NOT_EXIST,
            debug_message=message or "File Not Found",
            status_code=404,
        )


class InvalidUserAgentHeaderException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=message or "Invalid User Agent Header",
            status_code=400,
        )


class InvalidProjectIdException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_PROJECT_ID,
            debug_message=message or "Invalid project id",
            status_code=400,
        )


class InvalidClientIdException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_CLIENT_ID,
            debug_message=message or "Invalid client id",
            status_code=400,
        )


class UserAlreadyActiveException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.USER_ALREADY_ACTIVE,
            debug_message=message or "User is already active",
            status_code=400,
        )


class UserAlreadyOffboardedException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.USER_ALREADY_OFFBOARDED,
            debug_message=message or "User is already offboarded",
            status_code=400,
        )


class InternalServerErrorException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            debug_message=message or "Internal server error",
            status_code=500,
        )
