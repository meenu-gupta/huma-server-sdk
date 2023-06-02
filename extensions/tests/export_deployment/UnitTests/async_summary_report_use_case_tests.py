from unittest import TestCase
from unittest.mock import MagicMock, patch

from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import Deployment
from extensions.export_deployment.models.export_deployment_models import ExportProcess
from extensions.export_deployment.use_case.async_summary_report_use_case import (
    RunSummaryReportTaskUseCase,
)
from extensions.export_deployment.use_case.summary_report_request_objects import (
    GenerateSummaryReportRequestObject,
    ReportFormat,
)
from sdk.common.exceptions.exceptions import InvalidRequestException

USE_CASE_PATH = "extensions.export_deployment.use_case.async_summary_report_use_case"


class TestAsyncSummaryReportUseCase(TestCase):
    @patch(f"{USE_CASE_PATH}.ExportDeploymentRepository")
    def test_failure_run_async_summary_report(self, mock_repo):
        mock_repo.retrieve_export_processes = MagicMock()
        request_obj = self._sample_request_object()
        with self.assertRaises(InvalidRequestException):
            RunSummaryReportTaskUseCase(mock_repo).execute(request_obj)

    @patch(f"{USE_CASE_PATH}.ExportDeploymentRepository")
    @patch(f"{USE_CASE_PATH}.run_summary_report_generation", MagicMock())
    def test_success_run_async_summary_report(self, mock_repo):
        request_obj = self._sample_request_object()
        mock_repo.retrieve_export_processes = MagicMock(return_value=[])
        RunSummaryReportTaskUseCase(mock_repo).execute(request_obj)

    @patch(f"{USE_CASE_PATH}.ExportDeploymentRepository")
    @patch(f"{USE_CASE_PATH}.run_summary_report_generation", MagicMock())
    def test_success_run_async_summary_report_with_error_process(self, mock_repo):
        request_obj = self._sample_request_object()
        process = ExportProcess(status=ExportProcess.ExportStatus.ERROR)
        mock_repo.retrieve_export_processes = MagicMock(return_value=[process])
        RunSummaryReportTaskUseCase(mock_repo).execute(request_obj)

    @staticmethod
    def _sample_request_object():
        sample_id = "620cfed9367840eabbaf8ccb"
        user = User(id=sample_id)
        deployment = Deployment(name="Deployment", id=sample_id)
        request_obj = GenerateSummaryReportRequestObject.from_dict(
            {
                GenerateSummaryReportRequestObject.USER: user,
                GenerateSummaryReportRequestObject.DEPLOYMENT: deployment,
                GenerateSummaryReportRequestObject.REQUESTER_ID: sample_id,
                GenerateSummaryReportRequestObject.FORMAT: ReportFormat.PDF,
                GenerateSummaryReportRequestObject.START_DATE_TIME: "2022-04-30T06:55:56.653Z",
                GenerateSummaryReportRequestObject.END_DATE_TIME: "2022-05-05T06:55:56.650Z",
            }
        )
        return request_obj
