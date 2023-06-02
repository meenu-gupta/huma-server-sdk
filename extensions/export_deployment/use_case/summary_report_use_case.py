from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.common.file_utils import use_temp_file
from extensions.common.monitoring import report_exception
from extensions.export_deployment.models.export_deployment_models import ExportProcess
from extensions.export_deployment.pdf_report import CoverPage, html_to_pdf
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.use_case.summary_report_request_objects import (
    GenerateSummaryReportRequestObject,
    GenerateSummaryReportAsyncRequestObject,
)
from extensions.export_deployment.utils import notify_user_on_export_status
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.module_result.modules.visualizer import HTMLVisualizer
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.storage.use_case.storage_response_objects import DownloadFileResponseObject


class GenerateSummaryReportUseCase(UseCase):
    request_object: GenerateSummaryReportRequestObject
    jinja_env = Environment(
        loader=PackageLoader("extensions.export_deployment.pdf_report"),
        autoescape=select_autoescape(),
    )

    def process_request(self, _):
        bytes_data = self.generate_pdf()
        return DownloadFileResponseObject(
            content=bytes_data,
            content_length=len(bytes_data),
            content_type="application/pdf",
        )

    def generate_pdf(self) -> bytes:
        cover_letter_page = CoverPage(
            None,
            self.request_object.user,
            self.request_object.deployment,
            self.request_object.startDateTime,
            self.request_object.endDateTime,
        )
        cover_letter_page.jinja_env = self.jinja_env
        pages = [cover_letter_page]

        modules_manager = inject.instance(ModulesManager)
        for module in modules_manager.modules:
            try:
                page: HTMLVisualizer = module.get_visualizer(
                    user=self.request_object.user,
                    deployment=self.request_object.deployment,
                    start_date_time=self.request_object.startDateTime,
                    end_date_time=self.request_object.endDateTime,
                )
                pages.append(page)
            except RuntimeError:
                continue

        template = self.jinja_env.get_template("base.html")
        html = template.render(pages=pages, icon=self._get_icon_url())
        temp_filename = f"temp_{self.request_object.user.id}.html"
        file_path = Path(__file__).parent.joinpath(temp_filename)

        with use_temp_file(file_path):
            with open(file_path, "w") as file:
                file.write(html)

            return html_to_pdf(file_path)

    def _get_icon_url(self):
        deployment = self.request_object.deployment
        if not deployment.icon:
            return

        storage: FileStorageAdapter = inject.instance(FileStorageAdapter)
        return storage.get_pre_signed_url(deployment.icon.bucket, deployment.icon.key)


class GenerateSummaryReportAsyncUseCase(UseCase):
    """Use Case to run async report generation"""

    request_object: GenerateSummaryReportAsyncRequestObject

    @autoparams()
    def __init__(
        self,
        repo: ExportDeploymentRepository,
        auth_repo: AuthorizationRepository,
        storage: FileStorageAdapter,
    ):
        self._repo = repo
        self._auth_repo = auth_repo
        self._storage = storage

    def process_request(self, _):
        process = self.request_object.process
        bucket = self._get_export_bucket(process)
        timestamp = datetime.utcnow().isoformat()
        user_id = process.exportParams.userIds[0]
        filename = f"user/{user_id}/reports/{process.id}/{timestamp}.pdf"

        with self.keep_process_status_updated(process, bucket=bucket, key=filename):
            request_data = self._build_request_object(process)
            use_case = GenerateSummaryReportUseCase()
            file = use_case.execute(request_data).value

            return self._storage.upload_file(
                bucket, filename, file.content, file.contentLength, file.contentType
            )

    @contextmanager
    def keep_process_status_updated(self, process: ExportProcess, **kwargs):
        """Reports the status of the process based on what was the result of a body"""
        error = None
        self._update_process_status_to_progressing(process.id, **kwargs)
        try:
            yield
        except Exception as e:
            error = e
        finally:
            if error:
                notify_user_on_export_status(process, is_error=True)
                return self._update_process_status_to_error(process.id, error, **kwargs)
            notify_user_on_export_status(process)
            return self._update_process_status_to_done(process.id, **kwargs)

    def _update_process_status_to_progressing(self, process_id: str, **_):
        self._repo.update_export_process(
            process_id,
            ExportProcess.from_dict(
                {
                    ExportProcess.STATUS: ExportProcess.ExportStatus.PROCESSING.value,
                    ExportProcess.TASK_ID: self.request_object.taskId,
                }
            ),
        )

    def _update_process_status_to_error(self, process_id: str, error, **_):
        report_exception(
            error=error,
            context_name="ExportProcess",
            context_content={"exportProcessId": process_id},
        )
        self._repo.update_export_process(
            process_id,
            ExportProcess.from_dict(
                {
                    ExportProcess.STATUS: ExportProcess.ExportStatus.ERROR.value,
                    ExportProcess.SEEN: False,
                }
            ),
        )

    def _update_process_status_to_done(self, process_id: str, **kwargs):
        self._repo.update_export_process(
            process_id,
            ExportProcess.from_dict(
                {
                    ExportProcess.STATUS: ExportProcess.ExportStatus.DONE.value,
                    ExportProcess.SEEN: False,
                    ExportProcess.RESULT_OBJECT: kwargs,
                }
            ),
        )

    @autoparams("config")
    def _get_export_bucket(self, process, config: PhoenixServerConfig):
        return process.exportParams.exportBucket or config.server.storage.defaultBucket

    def _build_request_object(self, process: ExportProcess):
        user_id = process.exportParams.userIds[0]
        user = self._auth_repo.retrieve_simple_user_profile(user_id=user_id)
        deployment = AuthorizedUser(user, process.deploymentId).deployment
        return GenerateSummaryReportRequestObject(
            user=user,
            deployment=deployment,
            startDateTime=process.exportParams.fromDate,
            endDateTime=process.exportParams.toDate,
        )
