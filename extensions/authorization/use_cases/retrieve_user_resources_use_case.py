from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    RetrieveUserResourcesRequestObject,
)
from extensions.authorization.router.user_profile_response import (
    RetrieveUserResourcesResponseObject,
)
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrieveUserResourcesUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        repo: AuthorizationRepository,
        deployment_repo: DeploymentRepository,
        org_repo: OrganizationRepository,
    ):
        self._auth_repo = repo
        self._deployment_repo = deployment_repo
        self._org_repo = org_repo

    def process_request(
        self, request_object: RetrieveUserResourcesRequestObject
    ) -> Response:
        user = self._auth_repo.retrieve_simple_user_profile(
            user_id=request_object.userId
        )
        authz_user = AuthorizedUser(user)
        organizations = self._org_repo.retrieve_organizations_by_ids(
            organization_ids=authz_user.organization_ids()
        )
        deployment_ids = authz_user.deployment_ids()
        for org in organizations:
            if not org.deploymentIds:
                continue
            deployment_ids.extend(org.deploymentIds)

        deployments = self._deployment_repo.retrieve_deployments_by_ids(
            deployment_ids=list(set(deployment_ids))
        )

        return RetrieveUserResourcesResponseObject(
            deployments=deployments, organizations=organizations
        )
