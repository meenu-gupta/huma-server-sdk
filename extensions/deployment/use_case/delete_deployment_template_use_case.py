from extensions.authorization.models.role.role import RoleName
from extensions.deployment.models.deployment import TemplateCategory
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    DeleteDeploymentTemplateRequestObject,
)
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class DeleteDeploymentTemplateUseCase(UseCase):
    @autoparams()
    def __init__(self, repository: DeploymentRepository):
        self._repository = repository

    def process_request(self, request_object: DeleteDeploymentTemplateRequestObject):
        if request_object.submitter.role_assignment.roleId == RoleName.ACCOUNT_MANAGER:
            template = self._repository.retrieve_deployment_template(
                request_object.templateId
            )
            if template.category != TemplateCategory.SELF_SERVICE:
                raise PermissionDenied

        self._repository.delete_deployment_template(request_object.templateId)
        return Response()
