import unittest
from unittest.mock import MagicMock, patch, ANY

from sdk.common.adapter.identity_verification_mail_adapter import (
    IdentityVerificationEmailAdapter,
)

MAIL_ADAPTER_PATH = "sdk.common.adapter.identity_verification_mail_adapter"
TEST_EMAIL = "mail@test.com"


class IdentityVerificationMailAdapterTestCase(unittest.TestCase):
    @patch(f"{MAIL_ADAPTER_PATH}.logger", MagicMock())
    @patch(f"{MAIL_ADAPTER_PATH}.inject", MagicMock())
    def test_send_verification_result_email(self):
        mail_adapter = IdentityVerificationEmailAdapter(
            repo=MagicMock(), server_config=MagicMock(), email_adapter=MagicMock()
        )
        mail_adapter._email_adapter = MagicMock()

        mail_adapter.send_verification_result_email(to=TEST_EMAIL, username="user")
        mail_adapter._email_adapter.send_html_email.assert_called_with(
            to="mail@test.com", from_=ANY, subject=ANY, html=ANY
        )

    @patch(f"{MAIL_ADAPTER_PATH}.logger", MagicMock())
    @patch(f"{MAIL_ADAPTER_PATH}.inject", MagicMock())
    def test__extract_device_session(self):
        mail_adapter = IdentityVerificationEmailAdapter(
            repo=MagicMock(), server_config=MagicMock(), email_adapter=MagicMock()
        )
        mail_adapter._repo = MagicMock()

        mail_adapter._extract_device_session(
            email=TEST_EMAIL,
        )

        mail_adapter._repo.get_user.assert_called()
        mail_adapter._repo.retrieve_device_sessions_by_user_id.assert_called()

    @patch(f"{MAIL_ADAPTER_PATH}.logger")
    @patch(f"{MAIL_ADAPTER_PATH}.inject", MagicMock())
    def test__extract_device_session_exception(self, mock_logger):
        mail_adapter = IdentityVerificationEmailAdapter(
            repo=MagicMock(), server_config=MagicMock(), email_adapter=MagicMock()
        )
        mail_adapter._repo = MagicMock()

        mail_adapter._repo.retrieve_device_sessions_by_user_id.side_effect = Exception()

        mail_adapter._extract_device_session(
            email=TEST_EMAIL,
        )
        mock_logger.exception.assert_called()


if __name__ == "__main__":
    unittest.main()
