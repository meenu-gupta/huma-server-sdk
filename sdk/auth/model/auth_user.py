from dataclasses import field
from datetime import datetime
from enum import IntEnum, Enum

from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    validate_id,
    default_datetime_meta,
    validate_len,
    default_email_meta,
    default_phone_number_meta,
)


@convertibleclass
class AuthIdentifierType(IntEnum):
    PHONE_NUMBER = 1
    DEVICE_TOKEN = 2


@convertibleclass
class AuthIdentifier:
    TYPE = "type"
    VALUE = "value"
    VERIFIED = "verified"

    type: AuthIdentifierType = required_field()
    value: str = required_field()
    verified: bool = field(default=False)


@convertibleclass
class AuthKey:
    class AuthType(IntEnum):
        HAWK = 0

    AUTH_IDENTIFIER = "authIdentifier"
    AUTH_KEY = "authKey"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"
    ACTIVE = "active"
    AUTH_TYPE = "authType"

    authKey: str = required_field(metadata=meta(validate_len(64, 64)))
    authIdentifier: str = required_field(metadata=meta(validate_len(24, 24)))
    updateDateTime: datetime = required_field(metadata=default_datetime_meta())
    createDateTime: datetime = required_field(metadata=default_datetime_meta())
    active: bool = required_field(default=True)
    authType: AuthType = required_field()


@convertibleclass
class AuthUser:
    class Status(IntEnum):
        NORMAL = 1
        ARCHIVED = 2
        COMPROMISED = 3
        UNKNOWN = 4

    ID = "id"
    ID_ = "_id"
    STATUS = "status"
    EMAIL = "email"
    PHONE_NUMBER = "phoneNumber"
    HASHED_PASSWORD = "hashedPassword"
    PASSWORD_CREATE_DATE_TIME = "passwordCreateDateTime"
    PASSWORD_UPDATE_DATE_TIME = "passwordUpdateDateTime"
    DISPLAY_NAME = "displayName"
    VALIDATION_DATA = "validationData"
    USER_ATTRIBUTES = "userAttributes"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"
    EMAIL_VERIFIED = "emailVerified"
    PHONE_NUMBER_VERIFIED = "phoneNumberVerified"
    MFA_IDENTIFIERS = "mfaIdentifiers"
    MFA_ENABLED = "mfaEnabled"
    AUTH_KEYS = "authKeys"
    PREVIOUS_PASSWORDS = "previousPasswords"

    IGNORED_FIELDS = (
        PASSWORD_CREATE_DATE_TIME,
        PASSWORD_UPDATE_DATE_TIME,
        CREATE_DATE_TIME,
        UPDATE_DATE_TIME,
    )

    id: str = default_field(metadata=meta(validate_id))
    status: Status = default_field()
    emailVerified: bool = field(default=False)
    email: str = default_field(metadata=default_email_meta())
    phoneNumber: str = default_field(metadata=default_phone_number_meta())
    phoneNumberVerified: bool = default_field()
    hashedPassword: str = default_field(metadata=meta(validate_len(min=1)))
    previousPasswords: list[str] = default_field()
    passwordCreateDateTime: datetime = default_field(metadata=default_datetime_meta())
    passwordUpdateDateTime: datetime = default_field(metadata=default_datetime_meta())
    mfaEnabled: bool = field(default=False)
    displayName: str = default_field()
    validationData: dict = default_field()
    userAttributes: dict = default_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())

    mfaIdentifiers: list[AuthIdentifier] = default_field()
    authKeys: list[AuthKey] = default_field()

    @property
    def eligible_for_mfa(self):
        """Checks if all needed for Multi-Factor Auth process fields are set for user"""
        has_mfa_phone_number = self.has_mfa_identifier(AuthIdentifierType.PHONE_NUMBER)
        has_mfa_phone_number_verified = self.has_mfa_identifier_verified(
            AuthIdentifierType.PHONE_NUMBER
        )
        if (
            self.hashedPassword
            and has_mfa_phone_number
            and has_mfa_phone_number_verified
            and self.email
            and self.emailVerified
        ):
            return True
        return False

    def has_mfa_identifier(self, identifier_type: AuthIdentifierType):
        identifier = self.get_mfa_identifier(identifier_type)
        return True if identifier else False

    def has_mfa_identifier_verified(self, identifier_type: AuthIdentifierType):
        identifier = self.get_mfa_identifier(identifier_type)
        return True if (identifier and identifier.verified) else False

    def add_mfa_identifier(
        self, identifier_type: AuthIdentifierType, value: str, verified=False
    ):
        identifier = AuthIdentifier(
            type=identifier_type, value=value, verified=verified
        )
        if not self.mfaIdentifiers:
            self.mfaIdentifiers = [identifier]
        else:
            self.mfaIdentifiers.append(identifier)

    def get_mfa_identifier(
        self, identifier_type: AuthIdentifierType, value: str = None
    ):
        if self.mfaIdentifiers:
            for identifier in self.mfaIdentifiers:
                if identifier.type is not identifier_type:
                    continue
                if value is None:
                    return identifier
                if value == identifier.value:
                    return identifier

    def remove_mfa_identifier(
        self, identifier_type: AuthIdentifierType, value: str = None
    ):
        identifier = self.get_mfa_identifier(identifier_type, value)
        if identifier:
            self.mfaIdentifiers.remove(identifier)


class AuthAction(Enum):
    SignIn = "SignIn"
    RequestPasswordReset = "RequestPasswordReset"
    PasswordReset = "PasswordReset"
