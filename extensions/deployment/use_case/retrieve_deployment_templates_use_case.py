from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    RetrieveDeploymentTemplatesRequestObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrieveDeploymentTemplatesUseCase(UseCase):
    @autoparams()
    def __init__(self, repository: DeploymentRepository):
        self._repository = repository

    def process_request(self, request_object: RetrieveDeploymentTemplatesRequestObject):
        if request_object.organizationId:
            templates = self._repository.retrieve_deployment_templates(
                request_object.organizationId
            )
        else:
            templates = self._repository.retrieve_deployment_templates()
        return Response(value=templates)
