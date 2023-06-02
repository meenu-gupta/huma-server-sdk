"""Role model"""
from dataclasses import field

from extensions.authorization.models.role.default_permissions import (
    PERMISSIONS,
    PermissionType,
)
from extensions.deployment.exceptions import DuplicateRoleName
from sdk.common.exceptions.exceptions import RoleDoesNotExist
from sdk.common.utils.convertible import convertibleclass, meta, default_field
from sdk.common.utils.validators import validate_entity_name, validate_object_id


class RoleName:
    SUPER_ADMIN = "SuperAdmin"
    HUMA_SUPPORT = "HumaSupport"
    ACCOUNT_MANAGER = "AccountManager"
    ORGANIZATION_OWNER = "OrganizationOwner"
    ORGANIZATION_STAFF = "OrganizationStaff"
    ORGANIZATION_EDITOR = "OrganizationEditor"
    ACCESS_CONTROLLER = "AccessController"
    DEPLOYMENT_STAFF = "DeploymentStaff"
    ADMIN = "Admin"
    CONTRIBUTOR = "Contributor"
    CALL_CENTER = "CallCenter"
    USER = "User"
    PROXY = "Proxy"
    EXPORTER = "Exporter"
    MANAGER = "Manager"
    IDENTIFIABLE_EXPORT = "IdentifiableExport"
    SUPPORT = "Support"
    ADMINISTRATOR = "Administrator"
    SUPERVISOR = "Supervisor"
    CLINICIAN = "Clinician"

    @staticmethod
    def org_roles():
        return (
            RoleName.ACCESS_CONTROLLER,
            RoleName.ORGANIZATION_OWNER,
            RoleName.ORGANIZATION_EDITOR,
            RoleName.ORGANIZATION_STAFF,
            *RoleName.common_roles(),
        )

    @staticmethod
    def multi_deployment_roles():
        return (
            RoleName.DEPLOYMENT_STAFF,
            RoleName.CALL_CENTER,
            *RoleName.common_roles(),
        )

    @staticmethod
    def deployment_roles():
        return (
            *RoleName.multi_deployment_roles(),
            RoleName.SUPER_ADMIN,
            RoleName.HUMA_SUPPORT,
            RoleName.ACCOUNT_MANAGER,
            RoleName.ADMIN,
            RoleName.CONTRIBUTOR,
            RoleName.MANAGER,
            RoleName.USER,
            RoleName.PROXY,
            RoleName.EXPORTER,
            RoleName.IDENTIFIABLE_EXPORT,
        )

    @staticmethod
    def common_roles():
        return (
            RoleName.ADMINISTRATOR,
            RoleName.CLINICIAN,
            RoleName.SUPERVISOR,
            RoleName.SUPPORT,
        )


@convertibleclass
class Role:
    ID = "id"
    NAME = "name"
    PERMISSIONS = "permissions"
    USER_TYPE = "userType"

    class UserType:
        SUPER_ADMIN = "SuperAdmin"
        MANAGER = "Manager"
        USER = "User"
        PROXY = "Proxy"
        SERVICE_ACCOUNT = "ServiceAccount"

        @staticmethod
        def validate(value):
            return value in (
                Role.UserType.SUPER_ADMIN,
                Role.UserType.MANAGER,
                Role.UserType.USER,
                Role.UserType.PROXY,
                Role.UserType.SERVICE_ACCOUNT,
            )

        @staticmethod
        def non_managers():
            return (
                Role.UserType.SUPER_ADMIN,
                Role.UserType.USER,
                Role.UserType.PROXY,
                Role.UserType.SERVICE_ACCOUNT,
            )

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    name: str = default_field(metadata=meta(validate_entity_name))
    permissions: list[PermissionType] = default_field()
    userType: str = field(
        default=UserType.MANAGER, metadata=meta(validator=UserType.validate)
    )

    def has(self, policies: list) -> bool:
        if not self.permissions:
            return False

        user_policies = []
        for perm_type in self.permissions:
            permission_policy = PERMISSIONS.get(perm_type.value)
            if permission_policy and permission_policy.policies:
                user_policies.extend(permission_policy.policies)
        return all(policy in user_policies for policy in policies if policy)

    def is_new(self):
        return self.id is None

    def post_init(self):
        self.add_permissions(PermissionType.common_permissions())
        self.remove_duplicate_permissions()

    def add_permissions(self, permissions: list[PermissionType]):
        self.permissions.extend(permissions)
        self.remove_duplicate_permissions()

    def remove_duplicate_permissions(self):
        permissions = list(set(self.permissions))
        permissions.sort()
        self.permissions = permissions

    def has_extra_permissions(self) -> bool:
        return self.permissions != PermissionType.common_permissions()

    def __str__(self):
        return (
            f"[{Role.__name__} {Role.ID}: {self.id}, "
            f"{Role.NAME}: {self.name}, "
            f"{Role.PERMISSIONS}: {[permission.value for permission in self.permissions]}, "
            f"{Role.USER_TYPE}: {self.userType}]"
        )


@convertibleclass
class CustomRolesExtension:
    """Helper class to work with roles from deployment/organization."""

    ROLES = "roles"

    roles: list[Role] = default_field()

    def role_name_exists(self, role_name: str):
        role_names = {r.name for r in self.roles or []}
        return role_name in role_names

    def find_role_by_id(self, role_id: str):
        roles = self.roles or []
        return next((role for role in roles if role.id == role_id), None)

    def validate_roles(self, roles):
        for role in roles:
            if not role.id and self.role_name_exists(role.name):
                raise DuplicateRoleName
            if role.id and not self.find_role_by_id(role.id):
                raise RoleDoesNotExist
