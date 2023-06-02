from unittest import TestCase
from unittest.mock import MagicMock

from sdk.common.adapter.email_verification_adapter import EmailVerificationAdapter
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.phoenix.config.server_config import Client

SA_CLIENT = Client(clientType=Client.ClientType.SERVICE_ACCOUNT, clientId="sa_client")
TEST_EMAIL = "test@huma.com"
USERNAME = "user"


class EmailVerificationAdapterTestCase(TestCase):
    def setUp(self) -> None:
        self.otp_repo = MagicMock()
        self.server_config = MagicMock()
        self.server_config.server.project.notFoundLink = ""

        self.email_verification_adapter = EmailVerificationAdapter(
            self.otp_repo, self.server_config, email_adapter=MagicMock()
        )

    def test_error_send_verification_email(self):
        with self.assertRaises(InvalidRequestException):
            self.email_verification_adapter.send_verification_email(
                TEST_EMAIL, SA_CLIENT, USERNAME
            )
