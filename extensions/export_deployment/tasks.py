import logging
import os
import traceback
from datetime import datetime

from celery.schedules import crontab
from dateutil.relativedelta import relativedelta

from extensions.common.monitoring import report_exception
from extensions.export_deployment.exceptions import ExportProcessException
from extensions.export_deployment.models.export_deployment_models import (
    ExportProcess,
    ExportResultObject,
)
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
)
from extensions.export_deployment.use_case.summary_report_request_objects import (
    GenerateSummaryReportAsyncRequestObject,
)
from extensions.export_deployment.use_case.summary_report_use_case import (
    GenerateSummaryReportAsyncUseCase,
)
from extensions.export_deployment.utils import notify_user_on_export_status
from sdk.celery.app import celery_app
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


@celery_app.on_after_finalize.connect
def setup_delete_export_results_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute="*/5"),
        clean_user_export_results.s(),
        name="Async user export results cleaner",
    )
    sender.add_periodic_task(
        crontab(minute=0, hour="*/2"),
        mark_stuck_export_processes_as_failed.s(),
        name="Stuck export processes cleaner",
    )


def get_export_bucket(request_object, server_config: PhoenixServerConfig):
    return request_object.exportBucket or server_config.server.storage.defaultBucket


@autoparams("repo")
def mark_process_failed(process_id: str, repo: ExportDeploymentRepository):
    repo.update_export_process(
        process_id,
        ExportProcess(status=ExportProcess.ExportStatus.ERROR, seen=False),
    )


@celery_app.task(bind=True)
@autoparams("repo", "config")
def run_export(
    self,
    export_process_id: str,
    repo: ExportDeploymentRepository,
    config: PhoenixServerConfig,
):
    export_process = repo.retrieve_export_process(export_process_id)
    try:
        # To prevent circular import
        from extensions.export_deployment.use_case.export_use_cases import (
            ExportDeploymentUseCase,
        )

        # update status to PROCESSING
        repo.update_export_process(
            export_process_id,
            ExportProcess.from_dict(
                {
                    ExportProcess.STATUS: ExportProcess.ExportStatus.PROCESSING.value,
                    ExportProcess.TASK_ID: self.request.id,
                }
            ),
        )

        data = {
            **export_process.exportParams.to_dict(include_none=False),
            ExportRequestObject.DEPLOYMENT_ID: export_process.deploymentId,
            ExportRequestObject.DEPLOYMENT_IDS: export_process.deploymentIds,
            ExportRequestObject.ORGANIZATION_ID: export_process.organizationId,
        }
        request_object = ExportRequestObject.from_dict(remove_none_values(data))
        use_case = ExportDeploymentUseCase()
        export_data_archive_response = use_case.execute(request_object)
        timestamp = datetime.utcnow().isoformat()
        filename = f"user/{export_process.requesterId}/exports/{export_process_id}/{timestamp}.zip"

        # take export bucket from export config or first allowed bucket
        bucket = get_export_bucket(request_object, config)
        use_case.upload_result_to_bucket(
            filename,
            export_data_archive_response.value.content,
            export_data_archive_response.value.contentType,
            bucket,
        )
        # update status to DONE
        repo.update_export_process(
            export_process_id,
            ExportProcess(
                status=ExportProcess.ExportStatus.DONE,
                seen=False,
                resultObject={
                    ExportResultObject.BUCKET: bucket,
                    ExportResultObject.KEY: filename,
                },
            ),
        )
        notify_user_on_export_status(export_process)

    except Exception as e:
        logger.error(f"Export {export_process_id} error: {e}")
        report_exception(
            error=e,
            context_name="ExportProcess",
            context_content={
                "exportProcessId": export_process_id,
                "userId": export_process.requesterId,
            },
        )
        mark_process_failed(export_process_id)
        notify_user_on_export_status(export_process, is_error=True)


@celery_app.task(expires=5 * 60)
def clean_user_export_results():
    repo = inject.instance(ExportDeploymentRepository)
    export_processes = repo.retrieve_export_processes(
        export_type=[
            ExportProcess.ExportType.USER,
            ExportProcess.ExportType.SUMMARY_REPORT,
        ],
        status=ExportProcess.ExportStatus.DONE,
        till_date=datetime.utcnow() - relativedelta(days=7),
    )
    if not export_processes:
        return

    file_storage = inject.instance(FileStorageAdapter)
    for process in export_processes:
        try:
            folder = os.path.dirname(process.resultObject.key)
            file_storage.delete_folder(process.resultObject.bucket, folder)
            repo.delete_export_process(process.id)
        except Exception as e:
            logger.warning(
                f"Error deleting export {process.id} results: {e}. "
                f"Details: {traceback.format_exc()}"
            )


@celery_app.task
@autoparams("repo")
def mark_stuck_export_processes_as_failed(repo: ExportDeploymentRepository):
    stuck_date = datetime.utcnow() - relativedelta(hours=2)
    stuck_processes = repo.retrieve_export_processes(
        till_date=stuck_date, status=ExportProcess.ExportStatus.PROCESSING
    )
    for process in stuck_processes:
        mark_process_failed(process.id)
        msg = f"Found stuck export process {process.id}"
        logger.error(msg)
        report_exception(
            error=ExportProcessException(msg),
            context_name="ExportProcess",
            context_content={"exportProcessId": process.id},
        )


@celery_app.task(bind=True)
@autoparams("repo")
def run_summary_report_generation(
    self, process_id: str, repo: ExportDeploymentRepository
):
    process = repo.retrieve_export_process(process_id)
    try:
        request_object = GenerateSummaryReportAsyncRequestObject(
            process, self.request.id
        )
        GenerateSummaryReportAsyncUseCase().execute(request_object)
    except Exception as error:
        mark_process_failed(process.id, repo)
        report_exception(
            error=error,
            context_name="ExportProcess",
            context_content={"exportProcessId": process_id, "taskId": self.request.id},
        )
