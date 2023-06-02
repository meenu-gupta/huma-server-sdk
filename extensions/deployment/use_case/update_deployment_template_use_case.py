from extensions.authorization.models.role.role import RoleName
from extensions.deployment.models.deployment import TemplateCategory
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    UpdateDeploymentTemplateRequestObject,
)
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class UpdateDeploymentTemplateUseCase(UseCase):
    @autoparams()
    def __init__(self, repository: DeploymentRepository):
        self._repository = repository

    def process_request(self, request_object: UpdateDeploymentTemplateRequestObject):
        self._validate_if_account_manager(
            request_object.submitter.role_assignment.roleId, request_object.templateId
        )
        created_id = self._repository.update_deployment_template(
            request_object.templateId, request_object.updateData
        )
        return Response(value=created_id)

    def _validate_if_account_manager(self, role_id: str, template_id: str):
        if role_id == RoleName.ACCOUNT_MANAGER:
            template = self._repository.retrieve_deployment_template(template_id)
            if template.category != TemplateCategory.SELF_SERVICE:
                raise PermissionDenied
