from flask import g, request

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.invitation import Invitation
from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.router.invitation_request_objects import (
    SendInvitationsRequestObject,
    RetrieveInvitationsRequestObject,
    DeleteInvitationsListRequestObject,
    ResendInvitationsListRequestObject,
    ResendInvitationsRequestObject,
)
from extensions.authorization.router.user_profile_request import (
    LinkProxyRequestObject,
    RetrieveProfilesRequestObject,
)
from extensions.authorization.validators import is_common_role
from extensions.common.monitoring import report_exception
from extensions.common.policies import (
    is_self_request,
    get_user_route_policy,
    submitter_and_target_have_same_resource,
    are_users_in_the_same_resource,
)
from extensions.exceptions import UserDoesNotExist
from sdk.common.exceptions.exceptions import (
    PermissionDenied,
    DetailedException,
)
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.common.utils.inject import autoparams


def get_default_profile_policy():
    return get_user_route_policy(
        user_policy=PolicyType.VIEW_OWN_PROFILE,
        manager_policy=PolicyType.VIEW_PATIENT_PROFILE,
    )


def get_invitations_policy():
    policy = PolicyType.INVITE_STAFFS
    body = request.json or {}
    role = body.get(SendInvitationsRequestObject.ROLE_ID)
    if role == RoleName.USER:
        policy = PolicyType.INVITE_PATIENTS
    elif role == RoleName.PROXY:
        patient_id = body.get(SendInvitationsRequestObject.PATIENT_ID)
        if g.authz_user:
            if g.authz_user.id == patient_id:
                policy = PolicyType.INVITE_OWN_PROXY
            else:
                policy = PolicyType.INVITE_PROXY_FOR_PATIENT

    return policy


def get_retrieve_profiles_policy():
    policy = PolicyType.VIEW_PATIENT_PROFILE
    body = request.json or {}
    role = body.get(RetrieveProfilesRequestObject.ROLE)
    authz_user: AuthorizedUser = g.authz_user
    if role == RoleName.MANAGER and is_common_role(authz_user.get_role().id):
        policy = PolicyType.VIEW_STAFF_LIST
    return policy


def admin_invitation_policy() -> PolicyType:
    authz_user: AuthorizedUser = g.authz_user
    if authz_user.get_role().userType != Role.UserType.SUPER_ADMIN:
        raise PermissionDenied
    return PolicyType.INVITE_SUPER_STAFF


@autoparams()
def get_resend_invitation_policy(invitation_repo: InvitationRepository):
    request_data = get_request_json_dict_or_raise_exception(request)
    invitations_code = ResendInvitationsRequestObject.from_dict(
        request_data
    ).invitationCode

    invitation = invitation_repo.retrieve_invitation(code=invitations_code)

    if is_proxy_self_request(invitation):
        return
    if not invitation_has_same_resource_as_submitter(invitation):
        raise PermissionDenied

    policy = PolicyType.INVITE_STAFFS
    if invitation.role_id == RoleName.USER:
        policy = PolicyType.INVITE_PATIENTS
    elif invitation.role_id == RoleName.PROXY:
        policy = PolicyType.INVITE_PROXY_FOR_PATIENT

    return policy


@autoparams()
def get_resend_invitation_list_policy(invitation_repo: InvitationRepository):
    request_data = get_request_json_dict_or_raise_exception(request)
    invitations_list = ResendInvitationsListRequestObject.from_dict(
        request_data
    ).invitationsList

    policies = []
    invitation_code_list = [
        invitation.invitationCode for invitation in invitations_list
    ]
    invitation_list = invitation_repo.retrieve_invitation_list_by_code_list(
        invitation_code_list
    )
    for invitation in invitation_list:
        if is_proxy_self_request(invitation):
            continue
        if not invitation_has_same_resource_as_submitter(invitation):
            raise PermissionDenied

        policy = PolicyType.INVITE_STAFFS
        if invitation.role_id == RoleName.USER:
            policy = PolicyType.INVITE_PATIENTS
        elif invitation.role_id == RoleName.PROXY:
            policy = PolicyType.INVITE_PROXY_FOR_PATIENT

        policies.append(policy)

    return policies


@autoparams()
def get_delete_invitation_policy(invitation_repo: InvitationRepository):
    inv_id = request.view_args.get("invitation_id")
    invitation = invitation_repo.retrieve_invitation(invitation_id=inv_id)
    if is_proxy_self_request(invitation):
        return
    if not invitation_has_same_resource_as_submitter(invitation):
        raise PermissionDenied

    policy = PolicyType.INVITE_STAFFS
    if invitation.role_id == RoleName.USER:
        policy = PolicyType.INVITE_PATIENTS
    elif invitation.role_id == RoleName.PROXY:
        policy = PolicyType.INVITE_PROXY_FOR_PATIENT

    return policy


@autoparams()
def get_delete_invitation_list_policy(invitation_repo: InvitationRepository):
    request_data = get_request_json_dict_or_raise_exception(request)
    invitation_id_list = DeleteInvitationsListRequestObject.from_dict(
        request_data
    ).invitationIdList

    policies = []
    for invitation_id in invitation_id_list:
        invitation = invitation_repo.retrieve_invitation(invitation_id=invitation_id)

        if is_proxy_self_request(invitation):
            continue
        if not invitation_has_same_resource_as_submitter(invitation):
            raise PermissionDenied

        policy = PolicyType.INVITE_STAFFS
        if invitation.role_id == RoleName.USER:
            policy = PolicyType.INVITE_PATIENTS
        elif invitation.role_id == RoleName.PROXY:
            policy = PolicyType.INVITE_PROXY_FOR_PATIENT

        policies.append(policy)

    return policies


def invitation_has_same_resource_as_submitter(invitation: Invitation):
    submitter: AuthorizedUser = g.authz_user
    resource_ids = [role.resource_id() for role in invitation.roles]
    if invitation.role.is_deployment():
        allowed = submitter.deployment_ids()
    elif invitation.role.is_org():
        allowed = submitter.organization_ids()
    elif invitation.role.is_proxy():
        allowed = submitter.deployment_ids()
        resource_ids = [invitation.roles[1].resource_id()]
    else:
        msg = f"Unsupported Invitation role {invitation.role.roleId}"
        exception = NotImplementedError(msg)
        report_exception(
            exception,
            context_name="RoleData",
            context_content=invitation.role.to_dict(),
        )
        raise PermissionDenied

    resources_match = all(r_id in allowed for r_id in resource_ids)
    return allowed == ["*"] or resources_match


def is_proxy_self_request(invitation: Invitation):
    submitter: AuthorizedUser = g.authz_user
    if invitation.roles[0].is_proxy():
        return invitation.roles[0].resource_id() == submitter.user.id
    return False


def get_list_invitations_policy():
    policy = PolicyType.INVITE_STAFFS
    body = request.json or {}
    role_type = body.get(RetrieveInvitationsRequestObject.ROLE_TYPE)
    if role_type == RetrieveInvitationsRequestObject.RoleType.USER.value:
        policy = PolicyType.INVITE_PATIENTS
    return policy


def get_update_profile_policy():
    return get_user_route_policy(
        user_policy=PolicyType.EDIT_OWN_PROFILE,
        manager_policy=PolicyType.EDIT_PATIENT_PROFILE,
    )


def deny_user_with_star_resource():
    if any("/*" in (role.resource or "") for role in g.user.roles):
        raise PermissionDenied


def get_assign_roles_policy():
    policy = PolicyType.ASSIGN_ROLES_TO_STAFF
    if is_self_request():
        return policy

    if not submitter_and_target_have_same_resource():
        raise PermissionDenied

    return policy


def get_own_resource_policy():
    policy = PolicyType.VIEW_OWN_RESOURCES
    if is_self_request():
        return policy
    raise PermissionDenied


def get_retrieve_personal_documents_policy():
    return get_user_route_policy(
        PolicyType.VIEW_OWN_DATA, PolicyType.VIEW_PATIENT_IDENTIFIER
    )


def get_retrieve_profile_policy():
    target_user: AuthorizedUser = g.authz_path_user
    if target_user.is_proxy_for_user(g.authz_user.id):
        return PolicyType.VIEW_PROXY_PROFILE
    return get_default_profile_policy()


@autoparams("auth_repo")
def retrieve_proxy(email: str, auth_repo: AuthorizationRepository):
    """Retrieve proxy by email or raise error with specific code if not found."""
    try:
        return auth_repo.retrieve_user(email=email)
    except UserDoesNotExist:
        raise DetailedException(
            code=300011,
            debug_message="User Doesn't Exist.",
            status_code=404,
        )


def get_assign_proxy_policy():
    authz_participant: AuthorizedUser = g.authz_path_user
    request_json = get_request_json_dict_or_raise_exception(request)
    proxy_email = request_json.get(LinkProxyRequestObject.PROXY_EMAIL)
    # forbid assign yourself
    if authz_participant.user.email == proxy_email:
        raise PermissionDenied

    proxy_user = retrieve_proxy(proxy_email)
    authz_proxy_user = AuthorizedUser(proxy_user, authz_participant.deployment_id())
    # forbid assign not proxy
    if not authz_proxy_user.is_proxy():
        raise PermissionDenied
    return PolicyType.EDIT_OWN_PROFILE


@autoparams("repo")
def manager_user_in_the_same_resource(
    user_id, policy_type, repo: AuthorizationRepository
):
    target_user = g.authz_path_user
    # in case not "user_id" was used for authz_path_user
    if target_user.id != user_id:
        user = repo.retrieve_simple_user_profile(user_id=user_id)
        target_user = AuthorizedUser(user)
    if not are_users_in_the_same_resource(target_user, g.authz_user):
        raise PermissionDenied
    return policy_type


def get_read_policy():
    if is_self_request():
        return PolicyType.VIEW_OWN_EVENTS
    if not g.authz_user.is_manager():
        raise PermissionDenied

    user_id = request.view_args.get("user_id")
    return manager_user_in_the_same_resource(
        user_id, [PolicyType.VIEW_PATIENT_DATA, PolicyType.SCHEDULE_AND_CALL_PATIENT]
    )
