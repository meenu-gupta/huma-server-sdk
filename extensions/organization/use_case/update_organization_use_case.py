from extensions.organization.router.organization_requests import (
    UpdateOrganizationRequestObject,
)
from extensions.organization.use_case.base_organization_use_case import (
    BaseOrganizationUseCase,
)
from sdk.common.usecase.response_object import Response


class UpdateOrganizationUseCase(BaseOrganizationUseCase):
    def process_request(self, request_object: UpdateOrganizationRequestObject):
        if request_object.name:
            self._validate_organization_name(request_object.id, request_object.name)
        inserted_id = self.repo.update_organization(organization=request_object)

        return Response(inserted_id)

    def _validate_organization_name(self, org_id: str, org_name: str):
        org_before_update = self.repo.retrieve_organization(organization_id=org_id)
        if org_before_update.name.lower() != org_name.lower():
            self._validate_no_organization_with_same_name(org_name)
