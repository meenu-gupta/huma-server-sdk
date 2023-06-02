from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    RetrieveDeploymentTemplateRequestObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrieveDeploymentTemplateUseCase(UseCase):
    @autoparams()
    def __init__(self, repository: DeploymentRepository):
        self._repository = repository

    def process_request(self, request_object: RetrieveDeploymentTemplateRequestObject):
        template = self._repository.retrieve_deployment_template(
            request_object.templateId
        )
        return Response(value=template)
