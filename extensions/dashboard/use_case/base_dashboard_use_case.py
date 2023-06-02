from extensions.dashboard.models.dashboard import DashboardResourceType
from extensions.dashboard.repository.dashobard_repository import DashboardRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class BaseDashboardUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        repo: DashboardRepository,
        org_repo: OrganizationRepository,
        deployment_repo: DeploymentRepository,
    ):
        self._repo = repo
        self._org_repo = org_repo
        self._deployment_repo = deployment_repo

    def process_request(self, request_object):
        raise NotImplementedError

    def _get_resource(self, request_object):
        if request_object.resourceType == DashboardResourceType.ORGANIZATION:
            return self._org_repo.retrieve_organization(
                organization_id=request_object.resourceId
            )

        elif request_object.resourceType == DashboardResourceType.DEPLOYMENT:
            return self._deployment_repo.retrieve_deployment(
                deployment_id=request_object.resourceId
            )

        raise NotImplementedError(
            f"Only {DashboardResourceType.ORGANIZATION.value} or {DashboardResourceType.DEPLOYMENT.value} are supported"
        )
