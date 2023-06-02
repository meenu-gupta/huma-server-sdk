from extensions.authorization.models.user import User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class BaseAuthorizationUseCase(UseCase):
    request_object = None

    @autoparams()
    def __init__(
        self,
        repo: AuthorizationRepository,
        deployment_repo: DeploymentRepository,
        organization_repo: OrganizationRepository,
    ):
        self.auth_repo = repo
        self.deployment_repo = deployment_repo
        self.organization_repo = organization_repo

    def process_request(self, request_object):
        raise NotImplementedError

    def _inject_assigned_managers_ids_to_users(self, users: list[User]):
        user_ids = {user.id for user in users}
        result = self.auth_repo.retrieve_assigned_managers_ids_for_multiple_users(
            user_ids
        )
        for user in users:
            user.assignedManagers = result.get(user.id, [])
