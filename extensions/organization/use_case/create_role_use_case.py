from extensions.authorization.models.role.role import Role
from extensions.organization.models.organization import Organization
from extensions.organization.router.organization_requests import (
    OrganizationRoleUpdateObject,
)
from extensions.organization.use_case.base_organization_use_case import (
    BaseOrganizationUseCase,
)
from sdk.common.usecase.response_object import Response


class CreateOrUpdateRolesUseCase(BaseOrganizationUseCase):
    def process_request(self, request_object: OrganizationRoleUpdateObject):
        organization = self.repo.retrieve_organization(
            organization_id=request_object.organizationId
        )
        self._check_valid_roles(request_object.roles, organization)
        updated_ids = self.repo.create_or_update_roles(
            organization_id=request_object.organizationId, roles=request_object.roles
        )
        return Response(updated_ids)

    @staticmethod
    def _check_valid_roles(roles: list[Role], organization: Organization):
        organization.validate_roles(roles)
