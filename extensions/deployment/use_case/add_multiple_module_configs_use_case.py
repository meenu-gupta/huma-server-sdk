from extensions.deployment.router.deployment_requests import (
    CreateMultipleModuleConfigsRequestObject,
)
from extensions.deployment.service.deployment_service import DeploymentService
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase


class CreateMultipleModuleConfigsUseCase(UseCase):
    def process_request(
        self, request_object: CreateMultipleModuleConfigsRequestObject
    ) -> Response:
        service = DeploymentService()
        updated_ids = []
        for module_config in request_object.moduleConfigs:
            module_config_id = service.create_module_config(
                request_object.deploymentId, module_config
            )
            updated_ids.append(module_config_id)

        return Response(updated_ids)
