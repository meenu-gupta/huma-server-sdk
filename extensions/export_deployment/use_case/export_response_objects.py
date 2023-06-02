from typing import Union

from extensions.export_deployment.models.export_deployment_models import (
    ExportResultObject,
    ExportProcess,
    ExportProfile,
)
from sdk.common.usecase import response_object
from sdk.common.utils.convertible import convertibleclass, default_field, required_field


class ExportDeploymentResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        content: bytes = default_field()
        contentType: str = default_field()
        filename: str = default_field()

    def __init__(self, content: bytes, content_type: str, filename: str):
        super().__init__(
            value=self.Response(
                content=content,
                contentType=content_type,
                filename=filename,
            )
        )


class RunExportDeploymentTaskResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        exportProcessId: str = default_field()

    def __init__(self, export_process_io: str):
        super().__init__(
            value=self.Response(
                exportProcessId=export_process_io,
            )
        )


class CheckExportDeploymentTaskStatusResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        status: ExportProcess.ExportStatus = default_field()
        exportData: ExportResultObject = default_field()

    def __init__(
        self, status: str, export_data_object: Union[ExportResultObject, None] = None
    ):
        super().__init__(
            value=self.Response(status=status, exportData=export_data_object)
        )


class RetrieveExportProcessesResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        exportProcesses: list[ExportProcess] = default_field()

    def __init__(self, export_processes: list[ExportProcess]):
        super().__init__(value=self.Response(exportProcesses=export_processes))


class ResultIdResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        id: str = default_field()

    def __init__(self, result_id: str):
        super().__init__(value=self.Response(id=result_id))


class CreateExportProfileResponseObject(ResultIdResponseObject):
    pass


class UpdateExportProfileResponseObject(ResultIdResponseObject):
    pass


class RetrieveExportProfilesResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        exportProfiles: list[ExportProfile] = default_field()

    def __init__(self, export_profiles: list[ExportProfile]):
        super().__init__(value=self.Response(exportProfiles=export_profiles))


@convertibleclass
class ConfirmExportBadgesResponseObject:
    UPDATED = "updated"

    updated: int = required_field()
