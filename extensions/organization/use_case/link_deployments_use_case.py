from extensions.deployment.service.deployment_service import DeploymentService
from extensions.organization.router.organization_requests import (
    LinkDeploymentsRequestObject,
    UpdateOrganizationTargetConsentedRequestObject,
)
from extensions.organization.use_case.link_deployment_use_case import (
    LinkDeploymentUseCase,
)
from extensions.organization.use_case.update_organization_target_consented_use_case import (
    UpdateOrganizationTargetConsentedUseCase,
)
from sdk.common.usecase.response_object import Response


class LinkDeploymentsUseCase(LinkDeploymentUseCase):
    def process_request(self, request_object: LinkDeploymentsRequestObject) -> Response:
        for deployment_id in request_object.deploymentIds:
            deployment = DeploymentService().retrieve_deployment(
                deployment_id=deployment_id
            )
            self.validate_unique_deployment(
                organization_id=request_object.organizationId, deployment=deployment
            )

        organization_id = self.repo.link_deployments(
            organization_id=request_object.organizationId,
            deployment_ids=request_object.deploymentIds,
        )
        req_obj = UpdateOrganizationTargetConsentedRequestObject.from_dict(
            {
                UpdateOrganizationTargetConsentedRequestObject.ORGANIZATION_ID: request_object.organizationId
            }
        )
        UpdateOrganizationTargetConsentedUseCase().execute(req_obj)

        return Response(organization_id)
