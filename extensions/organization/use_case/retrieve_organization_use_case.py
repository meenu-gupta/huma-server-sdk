from extensions.organization.use_case.base_organization_use_case import (
    BaseOrganizationUseCase,
)
from sdk.common.usecase.response_object import Response


class RetrieveOrganizationUseCase(BaseOrganizationUseCase):
    def process_request(self, request_object):
        organization = self.repo.retrieve_organization_with_deployment_data(
            organization_id=request_object.organizationId
        )

        return Response(organization)
