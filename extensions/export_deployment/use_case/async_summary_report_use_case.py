from extensions.export_deployment.models.export_deployment_models import (
    ExportProcess,
    ExportParameters,
)
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.tasks import run_summary_report_generation
from extensions.export_deployment.use_case.summary_report_request_objects import (
    GenerateSummaryReportRequestObject,
)
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RunSummaryReportTaskUseCase(UseCase):
    request_object: GenerateSummaryReportRequestObject

    @autoparams()
    def __init__(self, export_repo: ExportDeploymentRepository):
        self._repo = export_repo

    def process_request(self, _):
        self._validate()

        process_id = self.create_task_record()
        run_summary_report_generation.apply_async(kwargs={"process_id": process_id})
        return Response(process_id)

    def _validate(self):
        processes = self._repo.retrieve_export_processes(
            user_id=self.request_object.user.id,
            export_type=[ExportProcess.ExportType.SUMMARY_REPORT],
        )
        if not processes:
            return

        processes.sort(key=lambda p: p.updateDateTime, reverse=True)
        if processes[0].status is not ExportProcess.ExportStatus.ERROR:
            raise InvalidRequestException("Export process is already running")

    def create_task_record(self) -> str:
        process = ExportProcess(
            requesterId=self.request_object.requesterId,
            deploymentId=self.request_object.deployment.id,
            exportParams=ExportParameters(
                userIds=[self.request_object.user.id],
                fromDate=self.request_object.startDateTime,
                binaryOption=ExportParameters.BinaryDataOption.NONE,
                toDate=self.request_object.endDateTime,
                format=ExportParameters.DataFormatOption.PDF,
                layer=ExportParameters.DataLayerOption.FLAT,
                quantity=ExportParameters.DataQuantityOption.SINGLE,
                useFlatStructure=True,
                singleFileResponse=True,
                excludeFields=[],
                deIdentifyHashFields=["None"],
                deIdentifyRemoveFields=["None"],
            ),
            exportType=ExportProcess.ExportType.SUMMARY_REPORT,
            status=ExportProcess.ExportStatus.CREATED,
            seen=True,
        )
        return self._repo.create_export_process(process)
