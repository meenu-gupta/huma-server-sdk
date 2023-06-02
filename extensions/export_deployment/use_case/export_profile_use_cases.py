from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.use_case.export_request_objects import (
    CreateExportProfileRequestObject,
    UpdateExportProfileRequestObject,
    DeleteExportProfileRequestObject,
    RetrieveExportProfilesRequestObject,
)
from extensions.export_deployment.use_case.export_response_objects import (
    CreateExportProfileResponseObject,
    RetrieveExportProfilesResponseObject,
    UpdateExportProfileResponseObject,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


@autoparams("export_repo")
def get_default_export_profile(
    export_repo: ExportDeploymentRepository,
    deployment_id: str = None,
    organization_id: str = None,
):
    try:
        return export_repo.retrieve_export_profile(
            default=True, deployment_id=deployment_id, organization_id=organization_id
        )
    except ObjectDoesNotExist:
        return


class BaseExportProfileUseCase(UseCase):
    @autoparams()
    def __init__(self, export_repo: ExportDeploymentRepository):
        self._export_repo = export_repo

    def process_request(self, request_object):
        raise NotImplementedError


class CreateExportProfileUseCase(BaseExportProfileUseCase):
    def process_request(
        self, request_object: CreateExportProfileRequestObject
    ) -> CreateExportProfileResponseObject:
        previous_default = None
        if request_object.default:
            previous_default = get_default_export_profile(
                self._export_repo,
                request_object.deploymentId,
                request_object.organizationId,
            )

        profile_id = self._export_repo.create_export_profile(request_object)

        if previous_default:
            previous_default.default = False
            self._export_repo.update_export_profile(previous_default)

        return CreateExportProfileResponseObject(profile_id)


class UpdateExportProfileUseCase(BaseExportProfileUseCase):
    def process_request(
        self, request_object: UpdateExportProfileRequestObject
    ) -> UpdateExportProfileResponseObject:
        previous_default = None
        if request_object.default:
            previous_default = get_default_export_profile(
                self._export_repo,
                request_object.deploymentId,
                request_object.organizationId,
            )

        profile_id = self._export_repo.update_export_profile(request_object)

        if previous_default and previous_default.id != request_object.id:
            previous_default.default = False
            self._export_repo.update_export_profile(previous_default)

        return UpdateExportProfileResponseObject(profile_id)


class DeleteExportProfileUseCase(BaseExportProfileUseCase):
    def process_request(self, request_object: DeleteExportProfileRequestObject):
        self._export_repo.delete_export_profile(request_object.profileId)


class RetrieveExportProfilesUseCase(BaseExportProfileUseCase):
    def process_request(
        self, request_object: RetrieveExportProfilesRequestObject
    ) -> RetrieveExportProfilesResponseObject:
        profiles = self._export_repo.retrieve_export_profiles(
            request_object.nameContains,
            request_object.deploymentId,
            request_object.organizationId,
        )
        return RetrieveExportProfilesResponseObject(profiles)
