import unittest
from unittest.mock import MagicMock, patch

from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.export_deployment.email_notification import EmailUserExportStatusService
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.tasks import run_export
from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
)
from extensions.export_deployment.use_case.export_use_cases import (
    ExportDeploymentUseCase,
)
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import Client, PhoenixServerConfig

EMAIL_SERVICE_PATH = "extensions.export_deployment.email_notification"
EMAIL_CALL = "extensions.export_deployment.tasks.notify_user_on_export_status"
DEEP_LINK_URL = "http://localhost:3901"
DEPLOYMENT_ID = "61e6c37e4477e38fa0a70c56"
TEST_EMAIL = "test@huma.com"
SAMPLE_ID = "61e6c37e4477e38fa0a70c56"
USERNAME = "user"
LINK = "http://webapp.com/download-user-data"
NOT_FOUND_LINK = "https://huma.com/404"


class ExportEmailServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.server_config = MagicMock()
        self.auth_repo = MagicMock()
        self.email_adapter = MagicMock()
        self.service = EmailUserExportStatusService(
            self.auth_repo, self.server_config, self.email_adapter
        )

        def bind(binder):
            binder.bind(ExportDeploymentRepository, MagicMock())
            binder.bind(PhoenixServerConfig, MagicMock())
            binder.bind(DeploymentRepository, MagicMock())
            binder.bind(FileStorageAdapter, MagicMock())
            binder.bind(OrganizationRepository, MagicMock())
            binder.bind(AuthorizationRepository, MagicMock())

        inject.clear_and_configure(bind)

    @patch.object(ExportDeploymentUseCase, "execute")
    @patch.object(ExportRequestObject, "from_dict")
    @patch.object(ExportDeploymentUseCase, "upload_result_to_bucket")
    @patch.object(ExportDeploymentRepository, "update_export_process")
    def test_run_async_user_export(self, update_process, bucket, request_obj, execute):
        export_process_id = "some_id"
        with patch(EMAIL_CALL) as email_mock:
            run_export(export_process_id)
            email_mock.assert_called_once()

    @patch(f"{EMAIL_SERVICE_PATH}.TemplateParameters")
    @patch.object(EmailUserExportStatusService, "_get_client")
    def test_send_success_export_email(self, client, template_params):
        client.return_value = c = Client()
        c.deepLinkBaseUrl = "http://webapp.com"

        self.service.send_success_data_generation_email(
            user_id=SAMPLE_ID, username=USERNAME, to=TEST_EMAIL, locale=Language.EN
        )

        template_params.assert_called_with(
            textDirection="",
            title="Notification.export.title",
            subtitle="Notification.export.subtitle.success",
            body="Notification.export.body.success",
            buttonText="Notification.export.buttonText.success",
            buttonLink=LINK,
        )

    @patch(f"{EMAIL_SERVICE_PATH}.TemplateParameters")
    @patch.object(EmailUserExportStatusService, "_get_client")
    def test_send_error_export_email(self, client, template_params):
        client.return_value = c = Client()
        c.deepLinkBaseUrl = "http://webapp.com"

        self.service.send_failure_data_generation_email(
            user_id=SAMPLE_ID, username=USERNAME, to=TEST_EMAIL, locale=Language.EN
        )

        template_params.assert_called_with(
            textDirection="",
            title="Notification.export.title",
            subtitle="Notification.export.subtitle.error",
            body="Notification.export.body.error",
            buttonText="Notification.export.buttonText.error",
            buttonLink=LINK,
        )

    @patch(f"{EMAIL_SERVICE_PATH}.TemplateParameters")
    @patch.object(EmailUserExportStatusService, "_extract_device_session")
    def test_client_not_found(self, extract_device, template_params):
        extract_device.return_value = None
        self.service._project.notFoundLink = NOT_FOUND_LINK
        self.service.send_failure_data_generation_email(
            user_id=SAMPLE_ID, username=USERNAME, to=TEST_EMAIL, locale=Language.EN
        )
        template_params.assert_called_with(
            textDirection="",
            title="Notification.export.title",
            subtitle="Notification.export.subtitle.error",
            body="Notification.export.body.error",
            buttonText="Notification.export.buttonText.error",
            buttonLink=NOT_FOUND_LINK,
        )


if __name__ == "__main__":
    unittest.main()
