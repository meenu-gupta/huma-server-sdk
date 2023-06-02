from flask import g, request

from extensions.authorization.models.authorized_user import AuthorizedUser, ProxyStatus
from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.exceptions import ProxyUnlinkedException
from sdk.common.exceptions.exceptions import PermissionDenied


def is_self_request():
    """Returns True if person who sent request is the same person who's data is accessed."""
    submitter: AuthorizedUser = g.authz_user

    requested_user: AuthorizedUser = g.authz_path_user
    if not requested_user:
        return True
    return submitter.id == requested_user.id


def get_user_route_read_policy():
    return get_user_route_policy(
        PolicyType.VIEW_OWN_PROFILE,
        PolicyType.VIEW_PATIENT_PROFILE,
    )


def get_user_route_write_policy():
    return get_user_route_policy(
        PolicyType.EDIT_OWN_DATA,
        PolicyType.EDIT_PATIENT_DATA,
    )


def get_update_appointment_policy():
    if not is_self_request():
        raise PermissionDenied

    policy = PolicyType.EDIT_OWN_EVENTS
    if g.authz_user.is_manager():
        policy = PolicyType.RESCHEDULE_CALL
    return policy


def get_user_route_policy(user_policy, manager_policy):
    policy = user_policy
    target_user: AuthorizedUser = g.authz_path_user
    if not target_user:
        return policy
    if not is_self_request():
        check_proxy_permission()
        if not submitter_and_target_have_same_resource():
            raise PermissionDenied
        policy = manager_policy
    return policy


def check_proxy_permission(deployment_id: str = None):
    """Used to check if proxy has proper permissions for targeted deployment"""
    target_user: AuthorizedUser = g.authz_path_user
    if not target_user:
        return
    target_deployment_id = deployment_id or target_user.deployment_id()
    submitter: AuthorizedUser = g.authz_user
    is_proxy_for_target = submitter.is_proxy_for_user(target_user.id)
    have_same_deployment = submitter.deployment_id() == target_deployment_id
    no_deployment = submitter.deployment_id() is None
    if not submitter.is_proxy():
        return
    if submitter.get_proxy_link_status() == ProxyStatus.UNLINK:
        raise ProxyUnlinkedException
    if not is_proxy_for_target or not have_same_deployment or no_deployment:
        raise PermissionDenied


def submitter_and_target_have_same_resource():
    target_user: AuthorizedUser = g.authz_path_user
    if not target_user:
        return True

    submitter: AuthorizedUser = g.authz_user
    return are_users_in_the_same_resource(target_user, submitter)


def are_users_in_the_same_resource(
    user_1: AuthorizedUser, user_2: AuthorizedUser
) -> bool:
    resource_id = user_1.deployment_id()
    if resource_id:
        allowed = user_2.deployment_ids()
    else:
        resource_id = user_1.organization_id()
        allowed = user_2.organization_ids()

    if allowed == ["*"] or resource_id in allowed:
        return True
    return False


def deny_not_self():
    if not is_self_request():
        raise PermissionDenied


def get_off_board_policy():
    if not submitter_and_target_have_same_resource():
        raise PermissionDenied
    return PolicyType.OFF_BOARD_PATIENT


def get_read_write_policy(read_policy, write_policy):
    """Return value based on request method"""
    if request.method == "GET":
        return read_policy
    else:
        return write_policy


def get_generate_token_policy():
    if is_self_request() or g.authz_user.is_super_admin():
        return PolicyType.GENERATE_AUTH_TOKEN
    raise PermissionDenied


def custom_module_config_policy():
    if not submitter_and_target_have_same_resource():
        raise PermissionDenied

    return PolicyType.MANAGE_PATIENT_MODULE_CONFIG
