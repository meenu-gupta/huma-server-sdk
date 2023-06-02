from extensions.organization.router.organization_requests import (
    UnlinkDeploymentsRequestObject,
    UpdateOrganizationTargetConsentedRequestObject,
)
from extensions.organization.use_case.base_organization_use_case import (
    BaseOrganizationUseCase,
)
from extensions.organization.use_case.update_organization_target_consented_use_case import (
    UpdateOrganizationTargetConsentedUseCase,
)
from sdk.common.usecase.response_object import Response


class UnlinkDeploymentsUseCase(BaseOrganizationUseCase):
    def process_request(self, request_object: UnlinkDeploymentsRequestObject):
        self.repo.unlink_deployments(
            organization_id=request_object.organizationId,
            deployment_ids=request_object.deploymentIds,
        )
        req_obj = UpdateOrganizationTargetConsentedRequestObject.from_dict(
            {
                UpdateOrganizationTargetConsentedRequestObject.ORGANIZATION_ID: request_object.organizationId
            }
        )
        UpdateOrganizationTargetConsentedUseCase().execute(req_obj)

        return Response(request_object.organizationId)
