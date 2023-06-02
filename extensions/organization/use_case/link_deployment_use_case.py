from extensions.deployment.models.deployment import Deployment
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.exceptions import DeploymentCodeExists, DeploymentExists
from extensions.organization.router.organization_requests import (
    UpdateOrganizationTargetConsentedRequestObject,
)
from extensions.organization.use_case.base_organization_use_case import (
    BaseOrganizationUseCase,
)
from extensions.organization.use_case.update_organization_target_consented_use_case import (
    UpdateOrganizationTargetConsentedUseCase,
)
from sdk.common.usecase.response_object import Response


class LinkDeploymentUseCase(BaseOrganizationUseCase):
    def validate_unique_deployment(self, organization_id: str, deployment: Deployment):
        organization = self.repo.retrieve_organization(organization_id=organization_id)
        if not organization.deploymentIds:
            return

        if deployment.id in organization.deploymentIds:
            raise DeploymentExists

        deployments = DeploymentService().retrieve_deployments_by_ids(
            deployment_ids=organization.deploymentIds
        )
        if deployment.code and deployment.code in map(lambda d: d.code, deployments):
            raise DeploymentCodeExists(code=deployment.code)

    def process_request(self, request_object):
        deployment = DeploymentService().retrieve_deployment(
            deployment_id=request_object.deploymentId
        )
        self.validate_unique_deployment(
            organization_id=request_object.organizationId, deployment=deployment
        )

        organization_id = self.repo.link_deployment(
            organization_id=request_object.organizationId,
            deployment_id=deployment.id,
        )
        req_obj = UpdateOrganizationTargetConsentedRequestObject.from_dict(
            {
                UpdateOrganizationTargetConsentedRequestObject.ORGANIZATION_ID: request_object.organizationId
            }
        )
        UpdateOrganizationTargetConsentedUseCase().execute(req_obj)

        return Response(organization_id)
