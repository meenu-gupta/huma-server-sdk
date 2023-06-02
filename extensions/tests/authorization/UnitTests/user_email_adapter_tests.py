import unittest
from unittest.mock import MagicMock, patch

from extensions.authorization.adapters.user_email_adapter import UserEmailAdapter
from sdk.common.localization.utils import Language

SAMPLE_ID = "61e6c37e4477e38fa0a70c56"
USER_EMAIL_ADAPTER_PATH = "extensions.authorization.adapters.user_email_adapter"


class UserEmailAdapterTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.server_config = MagicMock()
        self.auth_repo = MagicMock()
        self.auth_repo.retrieve_device_sessions_by_user_id.return_value = []
        self.adapter = UserEmailAdapter(self.auth_repo, self.server_config, MagicMock())

    @patch(f"{USER_EMAIL_ADAPTER_PATH}.TemplateParameters")
    def test_send_reactivate_user_email_link(self, template_param):
        self.adapter.send_reactivate_user_email(
            user_id=SAMPLE_ID, to="a@test.com", username="a", locale=Language.EN
        )
        template_param.assert_called_with(
            textDirection="",
            title="ReactivateUser.title",
            subtitle="ReactivateUser.subtitle",
            body="ReactivateUser.body",
            buttonText="ReactivateUser.buttonText",
            buttonLink=f"{self.server_config.server.project.get_client_by_client_type().deepLinkBaseUrl}/login?source=reactivated",
        )

    @patch(f"{USER_EMAIL_ADAPTER_PATH}.TemplateParameters")
    def test_send_off_board_user_email(self, template_param):
        self.adapter.send_off_board_user_email(
            to="a@test.com", locale=Language.EN, contact_url=None
        )
        template_param.assert_called_with(
            textDirection="", subtitle="OffBoardUser.title", body="OffBoardUser.body"
        )


if __name__ == "__main__":
    unittest.main()
