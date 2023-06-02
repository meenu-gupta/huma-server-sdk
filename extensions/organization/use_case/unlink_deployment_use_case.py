from extensions.organization.router.organization_requests import (
    UpdateOrganizationTargetConsentedRequestObject,
)
from extensions.organization.use_case.base_organization_use_case import (
    BaseOrganizationUseCase,
)
from extensions.organization.use_case.update_organization_target_consented_use_case import (
    UpdateOrganizationTargetConsentedUseCase,
)


class UnlinkDeploymentUseCase(BaseOrganizationUseCase):
    def process_request(self, request_object):
        self.repo.unlink_deployment(
            organization_id=request_object.organizationId,
            deployment_id=request_object.deploymentId,
        )
        req_obj = UpdateOrganizationTargetConsentedRequestObject.from_dict(
            {
                UpdateOrganizationTargetConsentedRequestObject.ORGANIZATION_ID: request_object.organizationId
            }
        )
        UpdateOrganizationTargetConsentedUseCase().execute(req_obj)
