from unittest.mock import MagicMock

from sdk.auth.use_case.auth_request_objects import SignUpRequestObject
from sdk.common.adapter.email_confirmation_adapter import EmailConfirmationAdapter
from sdk.common.adapter.email_verification_adapter import EmailVerificationAdapter
from sdk.common.adapter.sms_verification_adapter import SmsVerificationAdapter

SIGNUP_GIVEN_NAME = "Tester"
CURRENT_PASSWORD = "Aa123456"


class MockSmsAdapter(SmsVerificationAdapter):
    send_verification_code = MagicMock()

    def __init__(self, code=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = code

    def verify_code(self, code: str, phone_number: str) -> bool:
        if not self.code:
            return True

        return True if self.code == code else False


class MockEmailAdapter(EmailVerificationAdapter):
    send_verification_email = MagicMock()

    def __init__(self, code=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = code

    def verify_code(self, code: str, email: str, code_type: str = None) -> bool:
        if not self.code:
            return True

        return True if self.code == code else False


class MockEmailConfirmationAdapter(EmailConfirmationAdapter):
    send_confirmation_email = MagicMock()
    send_reset_password_email = MagicMock()

    def __init__(self, code=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = code

    def verify_code(
        self, code: str, email: str, code_type: str, delete_code: bool = True
    ) -> bool:
        if not self.code:
            return True
        return True if self.code == code else False


def sample_sign_up_data(email="first@test.com"):
    return {
        SignUpRequestObject.METHOD: 2,
        SignUpRequestObject.EMAIL: email,
        SignUpRequestObject.PASSWORD: CURRENT_PASSWORD,
        SignUpRequestObject.VALIDATION_DATA: {"activationCode": "53924415"},
        SignUpRequestObject.USER_ATTRIBUTES: {
            "familyName": "hey",
            "givenName": SIGNUP_GIVEN_NAME,
            "dob": "1988-02-20",
            "gender": "MALE",
        },
        SignUpRequestObject.CLIENT_ID: "ctest1",
        SignUpRequestObject.PROJECT_ID: "ptest1",
    }
