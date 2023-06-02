from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    CreateDeploymentTemplateRequestObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class CreateDeploymentTemplateUseCase(UseCase):
    @autoparams()
    def __init__(self, repository: DeploymentRepository):
        self._repository = repository

    def process_request(self, request_object: CreateDeploymentTemplateRequestObject):
        created_id = self._repository.create_deployment_template(request_object)
        return Response(value=created_id)
