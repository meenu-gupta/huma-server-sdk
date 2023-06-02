from extensions.organization.router.organization_requests import (
    UpdateOrganizationTargetConsentedRequestObject,
)
from extensions.organization.use_case.base_organization_use_case import (
    BaseOrganizationUseCase,
)
from sdk.common.usecase.response_object import Response


class UpdateOrganizationTargetConsentedUseCase(BaseOrganizationUseCase):
    def process_request(
        self, request_object: UpdateOrganizationTargetConsentedRequestObject
    ):
        if org_ids := request_object.organizationIds:
            for org_id in set(org_ids):
                self._update_org_target_consented(org_id)
        elif org_id := request_object.organizationId:
            self._update_org_target_consented(org_id)

        return Response(request_object.organizationIds)

    def _update_org_target_consented(self, org_id: str):
        from extensions.deployment.service.deployment_service import DeploymentService

        organization = self.repo.retrieve_organization(organization_id=org_id)
        deployment_ids = organization.deploymentIds
        dashboard_configs = [
            d.dashboardConfiguration
            for d in DeploymentService().retrieve_deployments_by_ids(deployment_ids)
            if d.dashboardConfiguration
        ]
        if not dashboard_configs:
            return

        organization.targetConsented = sum(
            [c.targetConsented for c in dashboard_configs if c.targetConsented]
        )
        self.repo.update_organization(organization)
