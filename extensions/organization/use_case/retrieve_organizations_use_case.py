from extensions.organization.router.organization_requests import (
    RetrieveOrganizationsRequestObject,
)
from extensions.organization.router.organization_responses import (
    RetrieveOrganizationsResponseObject,
)
from extensions.organization.use_case.base_organization_use_case import (
    BaseOrganizationUseCase,
)


class RetrieveOrganizationsUseCase(BaseOrganizationUseCase):
    def process_request(self, request_object: RetrieveOrganizationsRequestObject):
        organizations, total = self.repo.retrieve_organizations(
            skip=request_object.skip,
            limit=request_object.limit,
            name_contains=request_object.nameContains,
            sort_fields=request_object.sort,
            search_criteria=request_object.searchCriteria,
            status=request_object.status,
        )

        return RetrieveOrganizationsResponseObject(
            items=[organization.to_dict() for organization in organizations],
            total=total,
            limit=request_object.limit,
            skip=request_object.skip,
        )
