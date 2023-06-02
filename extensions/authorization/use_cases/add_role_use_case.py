from typing import Union

from extensions.authorization.events.post_user_add_role_event import (
    PostUserAddRoleEvent,
)
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.user import RoleAssignment, User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import AddRolesRequestObject
from extensions.authorization.use_cases.base_authorization_use_case import (
    BaseAuthorizationUseCase,
)
from extensions.authorization.validators import (
    is_common_role,
    validate_common_role_edit_levels,
    validate_same_resource_level,
)
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import InvalidRoleException
from sdk.common.usecase.response_object import Response
from sdk.common.utils.common_functions_utils import find
from sdk.common.utils.inject import autoparams


class AddRolesUseCase(BaseAuthorizationUseCase):
    @autoparams()
    def __init__(
        self,
        repo: AuthorizationRepository,
        deployment_repo: DeploymentRepository,
        organization_repo: OrganizationRepository,
        default_roles: DefaultRoles,
    ):
        self._default_roles = default_roles
        super(AddRolesUseCase, self).__init__(repo, deployment_repo, organization_repo)

    def process_request(self, request_object: AddRolesRequestObject):
        user = self.auth_repo.retrieve_simple_user_profile(
            user_id=request_object.userId
        )
        if not is_common_role(request_object.submitter.get_role().id):
            self._validate_roles(user.roles)
        user_roles: list[RoleAssignment] = user.roles[:]
        old_role_name = self._get_role_name(user_roles[0]) if user_roles else None
        for role in request_object.roles:
            self.add_role_to_list(role, user_roles)

        self._update_user_roles(user.id, user_roles)
        deployment_name = None
        if len(user_roles) >= 2:
            new_assigned_role = user_roles[-1]
            deployment = self.deployment_repo.retrieve_deployment(
                deployment_id=new_assigned_role.resource_id()
            )
            old_role_name = None
            new_role_name = self._get_role_name(new_assigned_role, deployment)
            deployment_name = deployment.name
        else:
            only_assigned_role = user_roles[0]
            new_role_name = self._get_role_name(only_assigned_role)

        self._post_user_add_role_event(
            old_role_name, new_role_name, deployment_name, user
        )
        return Response(user.id)

    def add_role_to_list(self, role: RoleAssignment, roles: list[RoleAssignment]):
        same_role_id_exist = find(lambda r: r.roleId == role.roleId, roles)
        same_role_exist = any(True for r in roles if r == role)
        if role.is_multi_resource():
            if same_role_id_exist:
                if not same_role_exist:
                    roles.append(role)
                return

            multi_deployment_roles = [r for r in roles if r.is_multi_resource()]
            if multi_deployment_roles and not is_common_role(role.roleId):
                role_id = next(iter(r.roleId for r in multi_deployment_roles))
                msg = f"Role {role_id} can not be updated to {role.roleId}"
                raise InvalidRoleException(msg)

        roles.clear()
        roles.append(role)

    def _update_user_roles(self, user_id: str, roles) -> str:
        body = {User.ID: user_id, User.ROLES: roles}
        req_obj = User.from_dict(body, ignored_fields=(User.ROLES,))
        return self.auth_repo.update_user_profile(req_obj)

    def _retrieve_organization(self):
        if not self.request_object.role.is_org():
            return

        org_id = self.request_object.role.resource_id()
        return self.organization_repo.retrieve_organization(organization_id=org_id)

    def _get_role_name(
        self,
        role_assignment: RoleAssignment,
        resource: Union[Deployment, Organization, None] = None,
    ):
        role = self._default_roles.get(role_assignment.roleId)
        if not role:
            if not resource:
                if role_assignment.is_deployment() and role_assignment.resource_id():
                    resource = self.deployment_repo.retrieve_deployment(
                        deployment_id=role_assignment.resource_id()
                    )
                elif role_assignment.is_org() and role_assignment.resource_id():
                    resource = self.organization_repo.retrieve_organization(
                        organization_id=role_assignment.resource_id()
                    )

            if resource:
                role = resource.find_role_by_id(role_assignment.roleId)

        return self._default_roles.get_role_repr(role.name)

    def _validate_roles(self, user_roles: list[RoleAssignment]):
        for role in self.request_object.roles:
            for user_role in user_roles:
                validate_same_resource_level(user_role, role)

    @autoparams("event_bus")
    def _post_user_add_role_event(
        self,
        old_role: str,
        new_role: str,
        deployment_name: str,
        user: User,
        event_bus: EventBusAdapter,
    ):
        event = PostUserAddRoleEvent(
            submitter=self.request_object.submitter,
            user=user,
            new_role=new_role,
            old_role=old_role,
            resource_name=deployment_name,
        )
        event_bus.emit(event)
