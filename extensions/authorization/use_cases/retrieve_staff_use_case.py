from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    RetrieveStaffRequestObject,
)
from extensions.authorization.validators import is_common_role
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrieveStaffUseCase(UseCase):
    @autoparams()
    def __init__(
        self, repo: AuthorizationRepository, deployment_repo: DeploymentRepository
    ):
        self.auth_repo = repo
        self.deployment_repo = deployment_repo

    def process_request(self, request_object: RetrieveStaffRequestObject) -> Response:
        assigned_count_dict = self.auth_repo.retrieve_assigned_patients_count()
        common_role = is_common_role(request_object.submitter.get_role().id)
        profiles = self.auth_repo.retrieve_staff(
            request_object.organizationId, request_object.nameContains, common_role
        )
        deployment_ids = set()
        for user in profiles:
            user.assignedUsersCount = assigned_count_dict.get(user.id, 0)
            authz_user = AuthorizedUser(user)
            user.deployments = authz_user.deployment_ids(exclude_wildcard=True)
            deployment_ids.update(user.deployments)

        codes = self.deployment_repo.retrieve_deployment_codes(list(deployment_ids))
        for profile in profiles:
            profile.deployments = [codes.get(id_) or id_ for id_ in profile.deployments]
        return Response(profiles)
