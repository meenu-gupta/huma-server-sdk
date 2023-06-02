from functools import cached_property

from frozendict import frozendict

from .default_permissions import PermissionType
from .role import Role, RoleName


class DefaultRoles:
    def __init__(self):
        self.role_string_mapping = {
            RoleName.ACCESS_CONTROLLER: "Access Controller",
            RoleName.ACCOUNT_MANAGER: "Account Manager",
            RoleName.CALL_CENTER: "Patient support",
            RoleName.DEPLOYMENT_STAFF: "Deployment Staff",
            RoleName.ORGANIZATION_OWNER: "Organization Owner",
            RoleName.ORGANIZATION_EDITOR: "Organization Editor",
            RoleName.ORGANIZATION_STAFF: "Organization Staff",
            RoleName.SUPER_ADMIN: "Super Admin",
            RoleName.HUMA_SUPPORT: "Huma Support",
            RoleName.EXPORTER: "Exporter",
            RoleName.IDENTIFIABLE_EXPORT: "Identifiable Export",
            RoleName.SUPPORT: "Support",
            RoleName.ADMINISTRATOR: "Administrator",
            RoleName.SUPERVISOR: "Supervisor",
            RoleName.ADMIN: "Admin",
            RoleName.CLINICIAN: "Clinician",
        }

    def __contains__(self, item):
        return item in self.dict

    def __getitem__(self, item):
        return self.dict[item]

    def __iter__(self):
        return iter(self.dict.keys())

    def get(self, item, default=None):
        return self[item] if item in self else default

    def get_role_repr(self, role: str) -> str:
        return self.role_string_mapping.get(role, role)

    @cached_property
    def access_controller(self):
        return Role(
            id=RoleName.ACCESS_CONTROLLER,
            name=RoleName.ACCESS_CONTROLLER,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.ADD_STAFF_MEMBERS,
                PermissionType.ADD_PATIENTS,
                PermissionType.EDIT_ROLE_PERMISSIONS,
                PermissionType.EXPORT_PATIENT_DATA,
                PermissionType.MANAGE_LABELS,
                PermissionType.VIEW_PATIENT_DATA,
                PermissionType.VIEW_STAFF_LIST,
                PermissionType.VIEW_DASHBOARD,
            ),
            userType=Role.UserType.MANAGER,
        )

    @cached_property
    def account_manager(self):
        return Role(
            id=RoleName.ACCOUNT_MANAGER,
            name=RoleName.ACCOUNT_MANAGER,
            permissions=(
                PermissionType.CREATE_ORGANIZATION,
                PermissionType.VIEW_OWN_DATA,
                PermissionType.VIEW_OWN_RESOURCES,
                PermissionType.MANAGE_OWN_DATA,
                PermissionType.ADD_PATIENTS,
                PermissionType.MANAGE_DEPLOYMENT_TEMPLATE,
            ),
            userType=Role.UserType.SUPER_ADMIN,
        )

    @cached_property
    def admin(self):
        return Role(
            id=RoleName.ADMIN,
            name=RoleName.ADMIN,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.MANAGE_PATIENT_DATA,
                PermissionType.CONTACT_PATIENT,
                PermissionType.VIEW_PATIENT_DATA,
                PermissionType.VIEW_PATIENT_IDENTIFIER,
                PermissionType.MANAGE_OWN_EVENTS,
                PermissionType.EDIT_ROLE_PERMISSIONS,
                PermissionType.ADD_STAFF_MEMBERS,
                PermissionType.EXPORT_PATIENT_DATA,
                PermissionType.MANAGE_PATIENT_MODULE_CONFIG,
                PermissionType.MANAGE_LABELS,
            ),
            userType=Role.UserType.MANAGER,
        )

    @cached_property
    def deployment_staff(self):
        return Role(
            id=RoleName.DEPLOYMENT_STAFF,
            name=RoleName.DEPLOYMENT_STAFF,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.CONTACT_PATIENT,
                PermissionType.MANAGE_PATIENT_DATA,
                PermissionType.VIEW_PATIENT_DATA,
                PermissionType.VIEW_PATIENT_IDENTIFIER,
            ),
            userType=Role.UserType.MANAGER,
        )

    @cached_property
    def call_center(self):
        return Role(
            id=RoleName.CALL_CENTER,
            name=RoleName.CALL_CENTER,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.VIEW_PATIENT_DATA,
                PermissionType.VIEW_PATIENT_IDENTIFIER,
                PermissionType.EDIT_PATIENT_DATA,
                PermissionType.CONTACT_PATIENT,
                PermissionType.OFF_BOARD_PATIENT,
                PermissionType.MANAGE_PATIENT_EVENTS,
                PermissionType.INVITE_PROXY_FOR_PATIENT,
            ),
            userType=Role.UserType.MANAGER,
        )

    @cached_property
    def contributor(self):
        return Role(
            id=RoleName.CONTRIBUTOR,
            name=RoleName.CONTRIBUTOR,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.MANAGE_PATIENT_DATA,
                PermissionType.CONTACT_PATIENT,
                PermissionType.VIEW_PATIENT_DATA,
                PermissionType.VIEW_PATIENT_IDENTIFIER,
                PermissionType.MANAGE_OWN_EVENTS,
                PermissionType.EXPORT_PATIENT_DATA,
            ),
            userType=Role.UserType.MANAGER,
        )

    @cached_property
    def huma_support(self):
        return Role(
            id=RoleName.HUMA_SUPPORT,
            name=RoleName.HUMA_SUPPORT,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.MANAGE_DEPLOYMENT,
                PermissionType.ADD_STAFF_MEMBERS,
                PermissionType.ADD_SUPER_STAFF_MEMBERS,
                PermissionType.MANAGE_ORGANIZATION,
                PermissionType.ADD_PATIENTS,
                PermissionType.VIEW_DEPLOYMENT_KEY_ACTIONS,
                PermissionType.MANAGE_DEPLOYMENT_TEMPLATE,
            ),
            userType=Role.UserType.SUPER_ADMIN,
        )

    @cached_property
    def organization_owner(self):
        return Role(
            id=RoleName.ORGANIZATION_OWNER,
            name=RoleName.ORGANIZATION_OWNER,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.OPERATE_ORGANIZATION,
                PermissionType.MANAGE_DEPLOYMENT,
                PermissionType.ADD_STAFF_MEMBERS,
                PermissionType.ADD_SUPER_STAFF_MEMBERS,
                PermissionType.EDIT_ROLE_PERMISSIONS,
                PermissionType.DELETE_ORGANIZATION,
                PermissionType.VIEW_OWN_RESOURCES,
                PermissionType.ADD_PATIENTS,
                PermissionType.RETRIEVE_DEPLOYMENT_TEMPLATE,
            ),
            userType=Role.UserType.SUPER_ADMIN,
        )

    @cached_property
    def organization_editor(self):
        return Role(
            id=RoleName.ORGANIZATION_EDITOR,
            name=RoleName.ORGANIZATION_EDITOR,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.OPERATE_ORGANIZATION,
                PermissionType.EDIT_DEPLOYMENT,
                PermissionType.ADD_STAFF_MEMBERS,
                PermissionType.EDIT_ROLE_PERMISSIONS,
                PermissionType.VIEW_OWN_RESOURCES,
                PermissionType.ADD_PATIENTS,
                PermissionType.RETRIEVE_DEPLOYMENT_TEMPLATE,
            ),
            userType=Role.UserType.SUPER_ADMIN,
        )

    @cached_property
    def organization_staff(self):
        return Role(
            id=RoleName.ORGANIZATION_STAFF,
            name=RoleName.ORGANIZATION_STAFF,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.EXPORT_PATIENT_DATA,
                PermissionType.MANAGE_LABELS,
                PermissionType.VIEW_PATIENT_DATA,
                PermissionType.VIEW_STAFF_LIST,
                PermissionType.VIEW_DASHBOARD,
            ),
            userType=Role.UserType.MANAGER,
        )

    @property
    def super_admin(self):
        return Role(
            id=RoleName.SUPER_ADMIN,
            name=RoleName.SUPER_ADMIN,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.EDIT_ROLE_PERMISSIONS,
                PermissionType.ADD_STAFF_MEMBERS,
                PermissionType.ADD_SUPER_STAFF_MEMBERS,
                PermissionType.MANAGE_DEPLOYMENT,
                PermissionType.EXPORT_PATIENT_DATA,
                PermissionType.MANAGE_ORGANIZATION,
                PermissionType.DELETE_ORGANIZATION,
                PermissionType.REMOVE_USER,
                PermissionType.ADD_PATIENTS,
                PermissionType.PUBLISH_PATIENT_DATA,
                PermissionType.VIEW_DEPLOYMENT_KEY_ACTIONS,
                PermissionType.MANAGE_DEPLOYMENT_TEMPLATE,
            ),
            userType=Role.UserType.SUPER_ADMIN,
        )

    @property
    def support(self):
        return Role(
            id=RoleName.SUPPORT,
            name=RoleName.SUPPORT,
            permissions=(
                PermissionType.CONTACT_PATIENT,
                PermissionType.EDIT_PATIENT_DATA,
                PermissionType.MANAGE_OWN_DATA,
                PermissionType.MANAGE_OWN_EVENTS,
                PermissionType.VIEW_OWN_DATA,
                PermissionType.VIEW_PATIENT_DATA,
                PermissionType.VIEW_PATIENT_IDENTIFIER,
            ),
            userType=Role.UserType.MANAGER,
        )

    @cached_property
    def administrator(self):
        return Role(
            id=RoleName.ADMINISTRATOR,
            name=RoleName.ADMINISTRATOR,
            permissions=(
                PermissionType.EDIT_ROLE_PERMISSIONS,
                PermissionType.ADD_STAFF_MEMBERS,
                PermissionType.ADD_PATIENTS,
                PermissionType.EXPORT_PATIENT_DATA,
                PermissionType.VIEW_STAFF_LIST,
                PermissionType.VIEW_PATIENT_DATA,
                PermissionType.VIEW_OWN_DATA,
                PermissionType.MANAGE_OWN_DATA,
                PermissionType.MANAGE_LABELS,
            ),
            userType=Role.UserType.MANAGER,
        )

    @cached_property
    def supervisor(self):
        return Role(
            id=RoleName.SUPERVISOR,
            name=RoleName.SUPERVISOR,
            permissions=(
                PermissionType.EXPORT_PATIENT_DATA,
                PermissionType.VIEW_STAFF_LIST,
                PermissionType.VIEW_PATIENT_DATA,
                PermissionType.VIEW_OWN_DATA,
                PermissionType.MANAGE_OWN_DATA,
            ),
            userType=Role.UserType.MANAGER,
        )

    @cached_property
    def clinician(self):
        return Role(
            id=RoleName.CLINICIAN,
            name=RoleName.CLINICIAN,
            permissions=(
                PermissionType.EXPORT_PATIENT_DATA,
                PermissionType.VIEW_PATIENT_DATA,
                PermissionType.MANAGE_PATIENT_DATA,
                PermissionType.CONTACT_PATIENT,
                PermissionType.VIEW_PATIENT_IDENTIFIER,
                PermissionType.INVITE_PROXY_FOR_PATIENT,
                PermissionType.MANAGE_PATIENT_EVENTS,
                PermissionType.VIEW_OWN_DATA,
                PermissionType.MANAGE_OWN_DATA,
                PermissionType.MANAGE_OWN_EVENTS,
                PermissionType.VIEW_STAFF_LIST,
            ),
            userType=Role.UserType.MANAGER,
        )

    @cached_property
    def user(self):
        return Role(
            id=RoleName.USER,
            name=RoleName.USER,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.GENERATE_HEALTH_REPORT,
                PermissionType.MANAGE_OWN_EVENTS,
                PermissionType.INVITE_OWN_PROXY,
            ),
            userType=Role.UserType.USER,
        )

    @cached_property
    def proxy(self):
        return Role(
            id=RoleName.PROXY,
            name=RoleName.PROXY,
            permissions=(
                *PermissionType.common_permissions(),
                PermissionType.MANAGE_OWN_EVENTS,
                PermissionType.VIEW_PATIENT_DATA,
                PermissionType.EDIT_PATIENT_DATA,
                PermissionType.VIEW_PATIENT_IDENTIFIER,
            ),
            userType=Role.UserType.PROXY,
        )

    @cached_property
    def dict(self):
        return frozendict(dict(**self.deployment) | dict(**self.organization))

    @cached_property
    def organization(self):
        return frozendict(
            {
                RoleName.ACCESS_CONTROLLER: self.access_controller,
                RoleName.ORGANIZATION_OWNER: self.organization_owner,
                RoleName.ORGANIZATION_EDITOR: self.organization_editor,
                RoleName.ORGANIZATION_STAFF: self.organization_staff,
                RoleName.DEPLOYMENT_STAFF: self.deployment_staff,
                RoleName.CALL_CENTER: self.call_center,
                RoleName.ADMINISTRATOR: self.administrator,
                RoleName.SUPERVISOR: self.supervisor,
                RoleName.SUPPORT: self.support,
                RoleName.CLINICIAN: self.clinician,
            }
        )

    @cached_property
    def deployment(self):
        return frozendict(
            {
                RoleName.SUPER_ADMIN: self.super_admin,
                RoleName.HUMA_SUPPORT: self.huma_support,
                RoleName.ACCOUNT_MANAGER: self.account_manager,
                RoleName.ADMIN: self.admin,
                RoleName.CONTRIBUTOR: self.contributor,
                RoleName.MANAGER: self.contributor,  # for backward compatibility
                RoleName.USER: self.user,
                RoleName.PROXY: self.proxy,
                RoleName.EXPORTER: self.exporter,
                RoleName.IDENTIFIABLE_EXPORT: self.identifiable_export,
                RoleName.ADMINISTRATOR: self.administrator,
                RoleName.SUPERVISOR: self.supervisor,
                RoleName.SUPPORT: self.support,
                RoleName.CLINICIAN: self.clinician,
            }
        )

    @cached_property
    def deployment_managers(self):
        return frozendict(
            {
                name: role
                for name, role in self.deployment.items()
                if role.userType == Role.UserType.MANAGER
            }
        )

    @cached_property
    def organization_managers(self):
        return frozendict(
            {
                name: role
                for name, role in self.organization.items()
                if role.userType == Role.UserType.MANAGER
            }
        )

    @cached_property
    def exporter(self):
        return Role(
            id=RoleName.EXPORTER,
            name=RoleName.EXPORTER,
            permissions=(PermissionType.EXPORT_PATIENT_DATA,),
            userType=Role.UserType.SERVICE_ACCOUNT,
        )

    @cached_property
    def identifiable_export(self):
        return Role(
            id=RoleName.IDENTIFIABLE_EXPORT,
            name=RoleName.IDENTIFIABLE_EXPORT,
            permissions=(
                PermissionType.EXPORT_PATIENT_DATA,
                PermissionType.VIEW_PATIENT_IDENTIFIER,
            ),
            userType=Role.UserType.SERVICE_ACCOUNT,
        )

    @cached_property
    def super_admins(self):
        return frozendict(
            {
                RoleName.SUPER_ADMIN: self.super_admin,
                RoleName.HUMA_SUPPORT: self.huma_support,
                RoleName.ACCOUNT_MANAGER: self.account_manager,
                RoleName.ORGANIZATION_OWNER: self.organization_owner,
                RoleName.ORGANIZATION_EDITOR: self.organization_editor,
            }
        )
