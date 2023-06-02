from dataclasses import field

from extensions.export_deployment.models.export_deployment_models import (
    ExportParameters,
    ExportProfile,
    ExportProcess,
)
from sdk.common.usecase import request_object
from sdk.common.utils.convertible import (
    convertibleclass,
    required_field,
    meta,
    default_field,
)
from sdk.common.utils.validators import (
    must_be_present,
    must_be_at_least_one_of,
    must_not_be_present,
    validate_object_id,
    str_id_to_obj_id,
    validate_object_ids,
)


@convertibleclass
class ExportRequestObject(ExportParameters):
    USE_EXPORT_PROFILE = "useExportProfile"
    DEPLOYMENT_ID = "deploymentId"
    BASE_PROFILE = "baseProfile"
    DO_TRANSLATE = "doTranslate"
    MANAGER_ID = "managerId"

    useExportProfile: bool = field(default=True)
    baseProfile: str = default_field()
    deploymentId: str = default_field(metadata=meta(validate_object_id))
    doTranslate: bool = field(default=True)
    managerId: str = default_field()

    @classmethod
    def validate(cls, request):
        must_be_at_least_one_of(
            deploymentId=request.deploymentId,
            deploymentIds=request.deploymentIds,
            organizationId=request.organizationId,
        )


@convertibleclass
class ExportUsersRequestObject(ExportRequestObject):
    deIdentified: bool = default_field()
    includeNullFields: bool = default_field()
    includeUserMetaData: bool = default_field()
    useFlatStructure: bool = default_field()
    view: ExportParameters.DataViewOption = default_field()
    format: ExportParameters.DataFormatOption = default_field()
    binaryOption: ExportParameters.BinaryDataOption = default_field()
    layer: ExportParameters.DataLayerOption = default_field()
    quantity: ExportParameters.DataQuantityOption = default_field()
    questionnairePerName: bool = default_field()
    splitMultipleChoice: bool = default_field()
    splitSymptoms: bool = default_field()
    translatePrimitives: bool = default_field()
    singleFileResponse: bool = default_field()
    excludeFields: list[str] = default_field()
    deIdentifyHashFields: list[str] = default_field()
    deIdentifyRemoveFields: list[str] = default_field()

    @classmethod
    def validate(cls, request):
        must_be_at_least_one_of(
            deploymentId=request.deploymentId,
            deploymentIds=request.deploymentIds,
            organizationId=request.organizationId,
        )
        must_not_be_present(
            deIdentifyHashFields=request.deIdentifyHashFields,
            deIdentifyRemoveFields=request.deIdentifyRemoveFields,
        )


@convertibleclass
class ExportUserDataRequestObject(ExportUsersRequestObject):
    USER_ID = "userId"

    format: ExportParameters.DataFormatOption = field(
        default=ExportParameters.DataFormatOption.CSV
    )
    view: ExportParameters.DataViewOption = field(
        default=ExportParameters.DataViewOption.MODULE_CONFIG
    )
    userId: str = required_field(
        metadata=meta(
            validate_object_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )

    @classmethod
    def validate(cls, request):
        must_not_be_present(
            excludeFields=request.excludeFields,
            deIdentifyHashFields=request.deIdentifyHashFields,
            deIdentifyRemoveFields=request.deIdentifyRemoveFields,
        )


@convertibleclass
class RunAsyncUserExportRequestObject(ExportUserDataRequestObject):
    REQUESTER_ID = "requesterId"

    requesterId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RunExportTaskRequestObject(ExportRequestObject):
    REQUESTER_ID = "requesterId"
    EXPORT_TYPE = "exportType"

    requesterId: str = required_field(metadata=meta(validate_object_id))
    exportType: ExportProcess.ExportType = field(
        default=ExportProcess.ExportType.DEFAULT
    )


@convertibleclass
class CheckExportDeploymentTaskStatusRequestObject(request_object.RequestObject):
    EXPORT_PROCESS_ID = "exportProcessId"
    DEPLOYMENT_ID = "deploymentId"

    exportProcessId: str = required_field(metadata=meta(validate_object_id))
    deploymentId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveExportDeploymentProcessesRequestObject(request_object.RequestObject):
    DEPLOYMENT_ID = "deploymentId"

    deploymentId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class CreateExportProfileRequestObject(ExportProfile):
    @classmethod
    def validate(cls, request):
        must_be_present(name=request.name, content=request.content)
        must_be_at_least_one_of(
            deploymentId=request.deploymentId, organizationId=request.organizationId
        )
        must_not_be_present(
            id=request.id,
            updateDateTime=request.updateDateTime,
            createDateTime=request.createDateTime,
        )


@convertibleclass
class UpdateExportProfileRequestObject(ExportProfile):
    @classmethod
    def validate(cls, request):
        must_be_at_least_one_of(
            deploymentId=request.deploymentId, organizationId=request.organizationId
        )
        must_not_be_present(
            updateDateTime=request.updateDateTime,
            createDateTime=request.createDateTime,
        )


@convertibleclass
class DeleteExportProfileRequestObject(request_object.RequestObject):
    DEPLOYMENT_ID = "deploymentId"
    PROFILE_ID = "profileId"

    deploymentId: str = default_field(metadata=meta(validate_object_id))
    organizationId: str = default_field(metadata=meta(validate_object_id))
    profileId: str = required_field(metadata=meta(validate_object_id))

    @classmethod
    def validate(cls, request):
        must_be_at_least_one_of(
            deploymentId=request.deploymentId, organizationId=request.organizationId
        )


@convertibleclass
class RetrieveExportProfilesRequestObject(request_object.RequestObject):
    DEPLOYMENT_ID = "deploymentId"
    ORGANIZATION_ID = "organizationId"
    NAME_CONTAINS = "nameContains"

    deploymentId: str = default_field(metadata=meta(validate_object_id))
    organizationId: str = default_field()
    nameContains: str = default_field()

    @classmethod
    def validate(cls, request):
        must_be_at_least_one_of(
            deploymentId=request.deploymentId, organizationId=request.organizationId
        )


@convertibleclass
class CheckUserExportTaskStatusRequestObject(request_object.RequestObject):
    EXPORT_PROCESS_ID = "exportProcessId"
    USER_ID = "userId"

    exportProcessId: str = required_field(metadata=meta(validate_object_id))
    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveUserExportProcessesRequestObject(request_object.RequestObject):
    USER_ID = "userId"

    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class ConfirmExportBadgesRequestObject(request_object.RequestObject):
    EXPORT_PROCESS_IDS = "exportProcessIds"
    REQUESTER_ID = "requesterId"

    exportProcessIds: list[str] = required_field(metadata=meta(validate_object_ids))
    requesterId: str = required_field(metadata=meta(validate_object_id))
