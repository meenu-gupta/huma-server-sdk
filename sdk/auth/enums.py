from enum import IntEnum


class Method(IntEnum):
    EMAIL = 0
    PHONE_NUMBER = 1
    EMAIL_PASSWORD = 2
    TWO_FACTOR_AUTH = 3


class AuthStage(IntEnum):
    NORMAL = 0
    FIRST = 1
    SECOND = 2
    REMEMBER_ME = 3


class SendVerificationTokenMethod(IntEnum):
    EMAIL = 0
    PHONE_NUMBER = 1
    EMAIL_SIGNUP_CONFIRMATION = 2
    TWO_FACTOR_AUTH = 3
    EXISTING_USER_EMAIL_CONFIRMATION = 4
