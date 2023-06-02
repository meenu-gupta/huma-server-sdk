from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    UpdateLocalizationsRequestObject,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams

from sdk.common.usecase.response_object import Response


class UpdateLocalizationsUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        deployment_repo: DeploymentRepository,
    ):
        self._deployment_repo = deployment_repo

    def process_request(self, request_object: UpdateLocalizationsRequestObject):
        updated_id = self._deployment_repo.update_localizations(
            deployment_id=request_object.deploymentId,
            localizations=request_object.localizations,
        )
        return Response(value=updated_id)
