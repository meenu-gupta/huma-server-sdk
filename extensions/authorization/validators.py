from extensions.authorization import helpers
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import RoleName
from extensions.exceptions import OrganizationDoesNotExist
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.exceptions.exceptions import InvalidRoleException
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams


@autoparams("org_repo")
def retrieve_organization(organization_id: str, org_repo: OrganizationRepository):
    try:
        return org_repo.retrieve_organization(organization_id=organization_id)
    except OrganizationDoesNotExist:
        return None


def check_role_id_valid_for_resource(
    role_id: str, resource_id: str, resource: str = None
):
    if resource in ("deployment", None):
        if role_id in RoleName.deployment_roles():
            return True

    if resource in ("organization", None):
        if role_id in RoleName.org_roles():
            return True

    return helpers.get_custom_role(role_id, resource_id, resource)


def check_role_id_valid_for_organization(role_id: str, organization_id: str):
    if role_id in RoleName.org_roles():
        return True

    organization = retrieve_organization(organization_id)
    return bool(organization and organization.find_role_by_id(role_id))


def is_common_role(role_id: str):
    return role_id in RoleName.common_roles()


def validate_common_role_edit_levels(submitter_resource: str, staff_resource: str):
    if not submitter_resource == "organization":
        if not staff_resource == "deployment":
            raise InvalidRoleException


def is_common_role_editable_role(role_id: str):
    if is_common_role(role_id):
        return True
    else:
        default_roles = inject.instance(DefaultRoles)
        if role_id in default_roles.dict.keys():
            return False
        return True  # custom role


def validate_same_resource_level(submitter_role, new_role):
    same_resource_level = is_same_resource_level(submitter_role, new_role)
    if not same_resource_level:
        msg = "Both target and submitter should be part of same resource level"
        raise InvalidRoleException(msg)


@autoparams("default_roles")
def is_same_resource_level(submitter_role, role, default_roles: DefaultRoles):
    if submitter_role.roleId == default_roles.super_admin.id:
        return True

    org_roles = default_roles.organization
    is_target_role_in_org = (
        role.roleId in org_roles
        or check_role_id_valid_for_organization(role.roleId, role.resource_id())
    )
    is_submitter_role_in_org = (
        submitter_role.roleId in org_roles
        or check_role_id_valid_for_organization(
            submitter_role.roleId, submitter_role.resource_id()
        )
    )

    return is_submitter_role_in_org == is_target_role_in_org
