from typing import Union

from extensions.authorization.events.post_user_add_role_event import (
    PostUserAddRoleEvent,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.user import RoleAssignment, User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    AddRolesToUsersRequestObject,
)
from extensions.authorization.use_cases.base_authorization_use_case import (
    BaseAuthorizationUseCase,
)
from extensions.authorization.validators import validate_same_resource_level
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import InvalidRoleException, PermissionDenied
from sdk.common.usecase.response_object import Response
from sdk.common.utils.common_functions_utils import find
from sdk.common.utils.inject import autoparams


class AddRolesToUsersUseCase(BaseAuthorizationUseCase):
    @autoparams()
    def __init__(
        self,
        repo: AuthorizationRepository,
        deployment_repo: DeploymentRepository,
        organization_repo: OrganizationRepository,
        default_roles: DefaultRoles,
    ):
        self._default_roles = default_roles
        super(AddRolesToUsersUseCase, self).__init__(
            repo, deployment_repo, organization_repo
        )

    def process_request(self, request_object: AddRolesToUsersRequestObject):
        new_roles = request_object.roles
        new_role_names = [role.roleId for role in new_roles]
        user_ids = request_object.userIds or []
        AddRolesToUsersRequestObject.check_permission(
            new_roles, request_object.submitter
        )
        if (
            len(user_ids) > 1 or request_object.allUsers
        ) and RoleName.ADMIN in new_role_names:
            raise PermissionDenied(
                f"{RoleName.ADMIN} role can't be set for multiple users at once"
            )

        users = (
            self._get_all_staff_members(request_object.submitter)
            if request_object.allUsers
            else self.auth_repo.retrieve_simple_user_profiles_by_ids(ids=user_ids)
        )
        for user in users:
            self._validate_roles(current_roles=user.roles, new_roles=new_roles)
            for role in new_roles:
                self.add_role_to_list(role, user.roles)

        self._update_users_roles(users)
        self._postprocess(users)

        return Response({"updatedUsers": len(users)})

    def add_role_to_list(self, role: RoleAssignment, roles: list[RoleAssignment]):
        same_role_id_exist = find(lambda r: r.roleId == role.roleId, roles)
        same_role_exist = role in roles
        if role.is_multi_resource():
            if same_role_id_exist:
                if not same_role_exist:
                    roles.append(role)
                return

            multi_deployment_roles = [r for r in roles if r.is_multi_resource()]
            if multi_deployment_roles:
                role_id = next(iter(r.roleId for r in multi_deployment_roles))
                msg = f"Role {role_id} can not be updated to {role.roleId}"
                raise InvalidRoleException(msg)

        roles.clear()
        roles.append(role)

    def _update_users_roles(self, users: list[User]):
        updated_users = [
            User.from_dict(
                {User.ID: user.id, User.ROLES: user.roles}, ignored_fields=(User.ROLES,)
            )
            for user in users
        ]
        self.auth_repo.update_user_profiles(updated_users)

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

    @staticmethod
    def _validate_roles(
        current_roles: list[RoleAssignment], new_roles: list[RoleAssignment]
    ):
        for new_role in new_roles:
            for current_role in current_roles:
                print(f"Current role: {current_role} New role: {new_role}")
                validate_same_resource_level(current_role, new_role)

    @autoparams("default_roles")
    def _get_all_staff_members(
        self, submitter: AuthorizedUser, default_roles: DefaultRoles
    ) -> list[User]:
        user_ids = self.auth_repo.retrieve_user_ids_in_deployment(
            deployment_id=submitter.deployment_id(),
            user_type=Role.UserType.MANAGER,
        )
        users = self.auth_repo.retrieve_simple_user_profiles_by_ids(ids=user_ids)
        staff_members = []
        org_roles = default_roles.organization
        for user in users:
            is_user_in_org = any(role.roleId in org_roles for role in user.roles)
            if not is_user_in_org and user.id != submitter.id:
                staff_members.append(user)
        return staff_members

    def _postprocess(self, users: list[User]):
        deployments_cache = {}
        for user in users:
            deployment_name = None
            old_role_name = self._get_role_name(user.roles[0]) if user.roles else None
            if len(user.roles) >= 2:
                new_assigned_role = user.roles[-1]
                resource_id = new_assigned_role.resource_id()
                deployment = deployments_cache.get(resource_id)
                if not deployment:
                    deployment = self.deployment_repo.retrieve_deployment(
                        deployment_id=resource_id
                    )
                    deployments_cache[resource_id] = deployment
                old_role_name = None
                new_role_name = self._get_role_name(new_assigned_role, deployment)
                deployment_name = deployment.name
            else:
                new_role_name = (
                    self._get_role_name(user.roles[0]) if user.roles else None
                )

            self._post_user_add_role_event(
                old_role_name, new_role_name, deployment_name, user
            )

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
