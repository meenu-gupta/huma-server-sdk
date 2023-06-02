from unittest.mock import patch

from extensions.export_deployment.models.export_deployment_models import ExportProcess
from extensions.export_deployment.tasks import run_export
from extensions.export_deployment.use_case.export_request_objects import (
    CheckUserExportTaskStatusRequestObject,
    ConfirmExportBadgesRequestObject,
)
from extensions.export_deployment.use_case.export_response_objects import (
    ConfirmExportBadgesResponseObject,
)
from extensions.export_deployment.use_case.export_use_cases import (
    ExportDeploymentUseCase,
)
from .export_deployment_router_tests import ExportTestCase, VIEW, USER_VIEW

EXISTING_TASK_ID = "61f04738d7b04d7039f3e437"


class UserExportTestCase(ExportTestCase):
    @patch("extensions.export_deployment.router.user_export_routers.g")
    @patch("extensions.export_deployment.tasks.run_export.apply_async")
    def test_run_async_user_export(self, mock_run_export_task, mock_g):
        mock_g.user.id = self.VALID_USER_ID
        data = {VIEW: USER_VIEW}
        url = f"/api/extensions/v1beta/export/user/{self.VALID_USER_ID}/task"
        resp = self.flask_client.post(url, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_process_id = resp.json.get(
            CheckUserExportTaskStatusRequestObject.EXPORT_PROCESS_ID
        )
        self.assertIsNotNone(export_process_id)
        mock_run_export_task.assert_called_once()

        with patch.object(ExportDeploymentUseCase, "execute") as mocked_export_execute:
            run_export(export_process_id)
        mocked_export_execute.assert_called_once()

    @patch("extensions.export_deployment.router.user_export_routers.g")
    def test_check_user_export_task(self, mock_g):
        url = f"/api/extensions/v1beta/export/user/{self.VALID_USER_ID}/task/{EXISTING_TASK_ID}"
        rsp = self.flask_client.get(url, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        expected_status = ExportProcess.ExportStatus.DONE.value
        self.assertEqual(expected_status, rsp.json[ExportProcess.STATUS])

    def retrieve_export_processes(self):
        url = f"/api/extensions/v1beta/export/user/{self.VALID_USER_ID}/task"
        rsp = self.flask_client.get(url, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        return rsp.json.get("exportProcesses", [])

    @patch("extensions.export_deployment.router.user_export_routers.g")
    def test_retrieve_check_user_export_task(self, mock_g):
        processes = self.retrieve_export_processes()
        self.assertEqual(1, len(processes))
        self.assertEqual(EXISTING_TASK_ID, processes[0][ExportProcess.ID])

    def test_mark_export_badges_seen(self):
        data = {ConfirmExportBadgesRequestObject.EXPORT_PROCESS_IDS: [EXISTING_TASK_ID]}
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/export/user/{self.VALID_USER_ID}/badges/confirm",
            json=data,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, rsp.json[ConfirmExportBadgesResponseObject.UPDATED])

        processes = self.retrieve_export_processes()
        self.assertTrue(processes[0][ExportProcess.SEEN])
