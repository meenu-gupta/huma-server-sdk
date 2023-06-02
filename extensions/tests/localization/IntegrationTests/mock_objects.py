from unittest.mock import MagicMock

from sdk.common.adapter.email_verification_adapter import EmailVerificationAdapter


class MockEmailAdapter(EmailVerificationAdapter):
    send_verification_email = MagicMock()

    def __init__(self, code=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = code

    def verify_code(self, code: str, email: str, code_type: str = None) -> bool:
        if not self.code:
            return True

        return True if self.code == code else False
