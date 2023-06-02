from pathlib import Path
from unittest.mock import MagicMock, patch

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.export_deployment.component import ExportDeploymentComponent
from extensions.export_deployment.models.export_deployment_models import (
    ExportProcess,
    ExportParameters,
)
from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
)
from extensions.export_deployment.use_case.export_response_objects import (
    CheckExportDeploymentTaskStatusResponseObject,
)
from extensions.export_deployment.use_case.export_use_cases import (
    ExportDeploymentUseCase,
    CheckExportTaskStatusUseCase,
)
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent

# admin of deployment
USER_WITH_IDENTIFIED_EXPORT_PERMISSIONS = "5e8f0c74b50aa9656c34789b"
# superadmin, as he can export only deidentified data
USER_WITH_EXPORT_PERMISSIONS = "5e8f0c74b50aa9656c34789a"
# user of deployment
USER_WITHOUT_EXPORT_PERMISSIONS = "5e8f0c74b50aa9656c34789c"

DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
EXPORT_PROCESS_ID = "5d386cc6ff885918d96edb2d"


def mocked_export_execute(self, request_object):
    response = MagicMock()
    response.value.content = b""
    return response


def mocked_export_check_process_execute(self, request_object):
    return CheckExportDeploymentTaskStatusResponseObject(
        ExportProcess.ExportStatus.DONE.value
    )


def get_export_process(self, process_id):
    export_params = ExportParameters()
    return ExportProcess(id=process_id, exportParams=export_params)


class ExportDeploymentPermissionTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ExportDeploymentComponent(),
        OrganizationComponent(),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/data.json"),
    ]
    override_config = {"server.exportDeployment.enableAuth": "true"}

    def setUp(self):
        super().setUp()

    def test_cannot_export_without_permission(self):
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}",
            headers=self.get_headers_for_token(USER_WITHOUT_EXPORT_PERMISSIONS),
        )
        self.assertEqual(403, rsp.status_code)

    def test_can_export_with_export_permission_deidentified(self):
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}",
            headers=self.get_headers_for_token(USER_WITH_EXPORT_PERMISSIONS),
        )
        self.assertEqual(403, rsp.status_code)

        with patch.object(ExportDeploymentUseCase, "execute", mocked_export_execute):
            data = {ExportRequestObject.DEIDENTIFIED: True}
            rsp = self.flask_client.post(
                f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}",
                headers=self.get_headers_for_token(USER_WITH_EXPORT_PERMISSIONS),
                json=data,
            )
            self.assertEqual(200, rsp.status_code)

    def test_can_export_with_export_permission_identified(self):
        with patch.object(ExportDeploymentUseCase, "execute", mocked_export_execute):
            rsp = self.flask_client.post(
                f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}",
                headers=self.get_headers_for_token(
                    USER_WITH_IDENTIFIED_EXPORT_PERMISSIONS
                ),
            )
            self.assertEqual(200, rsp.status_code)

            data = {ExportRequestObject.DEIDENTIFIED: True}
            rsp = self.flask_client.post(
                f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}",
                headers=self.get_headers_for_token(
                    USER_WITH_IDENTIFIED_EXPORT_PERMISSIONS
                ),
                json=data,
            )
            self.assertEqual(200, rsp.status_code)

    def test_check_identified_task_result_without_permission(self):
        url = f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}/task/{EXPORT_PROCESS_ID}"
        headers = self.get_headers_for_token(USER_WITH_EXPORT_PERMISSIONS)
        rsp = self.flask_client.get(url, headers=headers)
        self.assertEqual(403, rsp.status_code)

        with patch.object(
            CheckExportTaskStatusUseCase,
            "execute",
            mocked_export_check_process_execute,
        ):
            headers = self.get_headers_for_token(
                USER_WITH_IDENTIFIED_EXPORT_PERMISSIONS
            )
            rsp = self.flask_client.get(url, headers=headers)
            self.assertEqual(200, rsp.status_code)
