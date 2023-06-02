from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import DeleteLabelRequestObject
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class DeleteDeploymentLabelUseCase(UseCase):
    @autoparams()
    def __init__(
        self, repository: DeploymentRepository, auth_repo: AuthorizationRepository
    ):
        self._repository = repository
        self.auth_repo = auth_repo

    def process_request(self, request_object: DeleteLabelRequestObject):
        self._repository.delete_deployment_label(
            deployment_id=request_object.deploymentId, label_id=request_object.labelId
        )
        self.auth_repo.unassign_label_from_users(label_id=request_object.labelId)
        return Response()
