import logging
from datetime import datetime
from typing import Optional, Union

from flask import g, request
from i18n import t
from pymongo.client_session import ClientSession

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from extensions.authorization.adapters.user_email_adapter import UserEmailAdapter
from extensions.authorization.events import (
    PostCreateTagEvent,
    PostUnlinkProxyUserEvent,
    PostUserOffBoardEvent,
    PostUserProfileUpdateEvent,
    PostUserReactivationEvent,
)
from extensions.authorization.events.get_badges_event import GetUserBadgesEvent
from extensions.authorization.events.post_assign_label_event import PostAssignLabelEvent
from extensions.authorization.events.post_user_add_role_event import (
    PostUserAddRoleEvent,
)
from extensions.authorization.exceptions import (
    WrongActivationOrMasterKeyException,
    InvitationDoesNotExistException,
)
from extensions.authorization.middleware import AuthorizationMiddleware
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.label_log import LabelLog
from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.stats_calculator import UserStatsCalculator
from extensions.authorization.models.tag_log import TagLog
from extensions.authorization.models.user import BoardingStatus, RoleAssignment, User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    OffBoardUserRequestObject,
    UpdateUserProfileRequestObject,
    UnlinkProxyRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.authorization.use_cases.invitation_use_cases import retrieve_invitation
from extensions.authorization.use_cases.off_board_user_use_case import (
    OffBoardUserUseCase,
)
from extensions.common.policies import (
    is_self_request,
    get_read_write_policy,
    submitter_and_target_have_same_resource,
    get_generate_token_policy,
)
from extensions.deployment.events.delete_custom_roles_event import (
    DeleteDeploymentCustomRolesEvent,
)
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.deployment.models.deployment import Deployment, ReasonDetails
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.exceptions import ValidationDataError
from extensions.module_result.event_bus.post_create_module_results_batch_event import (
    PostCreateModuleResultBatchEvent,
)
from extensions.organization.events import (
    PostCreateOrganizationEvent,
    PostDeleteOrganizationEvent,
)
from sdk.auth.decorators import check_token_valid_for_mfa, check_auth
from sdk.auth.events.check_attributes_event import CheckAuthAttributesEvent
from sdk.auth.events.delete_user_event import DeleteUserEvent
from sdk.auth.events.generate_token_event import GenerateTokenEvent
from sdk.auth.events.post_sign_in_event import PostSignInEvent
from sdk.auth.events.post_sign_up_event import PostSignUpEvent
from sdk.auth.events.pre_sign_up_event import PreSignUpEvent
from sdk.auth.events.set_auth_attributes_events import (
    PostSetAuthAttributesEvent,
    PreSetAuthAttributesEvent,
    PreRequestPasswordResetEvent,
)
from sdk.auth.events.token_extraction_event import TokenExtractionEvent
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.use_case.auth_use_cases import get_client
from sdk.calendar.events import (
    CalendarViewUserDataEvent,
    CreateCalendarLogEvent,
    RequestUsersTimezonesEvent,
)
from sdk.calendar.models.calendar_view_user_data import CalendarViewUsersData
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.adapter.token.helper import verify_jwt_in_request
from sdk.common.exceptions.exceptions import (
    DetailedException,
    ErrorCodes,
    ClientPermissionDenied,
    InvalidRequestException,
    UnauthorizedException,
    MFARequiredException,
    PermissionDenied,
    ObjectDoesNotExist,
)
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values
from sdk.inbox.repo.inbox_repository import InboxRepository
from sdk.notification.events.auth_events import NotificationAuthEvent
from sdk.phoenix.config.server_config import Client, PhoenixServerConfig
from sdk.storage.callbacks.binder import PostStorageSetupEvent

logger = logging.getLogger(__name__)


def setup_storage_auth(_: PostStorageSetupEvent):
    filename = get_file_name_from_request()
    validate_filename(filename)
    resource, resource_id, filename = filename.split("/", 2)

    authz_user: AuthorizedUser = g.authz_user

    if resource == "deployment":
        policies = [PolicyType.EDIT_DEPLOYMENT]

        if request.method == "GET":
            policies = [PolicyType.VIEW_DEPLOYMENT]

            if authz_user.deployment_id() == resource_id:
                policies = [PolicyType.VIEW_OWN_DATA]
    elif resource == "user":
        policies = []
        if is_self_request() or authz_user.is_proxy_for_user(resource_id):
            policy = get_read_write_policy(
                PolicyType.VIEW_OWN_DATA,
                PolicyType.EDIT_OWN_DATA,
            )
            policies.append(policy)
        else:
            if not submitter_and_target_have_same_resource():
                raise PermissionDenied

            policy = get_read_write_policy(
                PolicyType.VIEW_PATIENT_DATA,
                PolicyType.EDIT_PATIENT_DATA,
            )
            policies.append(policy)
            if "PersonalDocuments/" in filename:
                policies.append(PolicyType.VIEW_PATIENT_IDENTIFIER)
    elif resource == "static":
        if not authz_user.is_super_admin():
            raise PermissionDenied
        return
    else:
        raise PermissionDenied

    IAMBlueprint.check_permissions(policies)


def get_file_name_from_request() -> str:
    filename_key = "filename"
    resource: dict = request.form
    if request.method == "GET":
        resource = request.view_args

    if not (file_name := resource.get(filename_key)):
        raise InvalidRequestException
    return file_name


def validate_filename(filename):
    msg = f"'{filename}' can not be analysed. Should have at least three parameters."
    if len(filename.split("/")) < 3:
        raise InvalidRequestException(msg)


def allow_ip_callback(event: PreSignUpEvent):
    try:
        master_key = event.validation_data.get("masterKey", None)
    except AttributeError:
        pass
    else:
        if (
            master_key
            and not AuthorizationService().check_ip_allowed_create_super_admin(
                master_key
            )
        ):
            raise DetailedException(
                ErrorCodes.FORBIDDEN_ID, debug_message="IP not allowed", status_code=403
            )


def on_token_extraction_callback(event: TokenExtractionEvent):
    AuthorizationMiddleware(request)(event.id)


def extract_user(user_id: str) -> User:
    user: User = g.get("user") or User()
    if user.id != user_id:
        user: User = g.get("path_user") or User()

    if user.id != user_id:
        user_service = AuthorizationService()
        user = user_service.retrieve_user_profile(user_id)
    return user


def check_if_participant_off_boarded(user: AuthorizedUser) -> bool:
    participants = user.get_assigned_participants()
    if participants:
        participant_id = next(iter(participants))[AuthorizedUser.USER_ID]
        participant = AuthorizationService().retrieve_simple_user_profile(
            participant_id
        )
        if participant.is_off_boarded():
            return True
    return False


def register_user_with_role(event: PostSignUpEvent):
    server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
    client = get_client(server_config.server.project, event.client_id)

    user = _prepare_new_user(event.to_dict(), client)
    authorized_user = AuthorizedUser(user)

    # checking client permission
    if not are_client_permissions_valid(client, authorized_user):
        raise ClientPermissionDenied

    if authorized_user.is_proxy():
        if check_if_participant_off_boarded(authorized_user):
            user.boardingStatus = BoardingStatus.from_dict(
                {BoardingStatus.STATUS: BoardingStatus.Status.OFF_BOARDED}
            )

    user.id = AuthorizationService().create_user(user, event.session)
    return user.to_dict(include_none=False)


def on_calendar_view_users_data_callback(
    _: CalendarViewUserDataEvent,
) -> CalendarViewUsersData:
    required_fields = {
        User.CREATE_DATE_TIME: "Sign Up Date",
        User.SURGERY_DATE_TIME: "Surgery Date",
    }
    users_data = (
        AuthorizationService().retrieve_users_with_user_role_including_only_fields(
            tuple(required_fields.keys()), to_model=False
        )
    )

    res_data = []
    for user in users_data:
        user[User.ID] = str(user.pop(User.ID_))
        res_data.append(user)

    return CalendarViewUsersData(additional_fields=required_fields, users_data=res_data)


def check_valid_client_used(
    event: Union[
        PostSignInEvent, CheckAuthAttributesEvent, PreRequestPasswordResetEvent
    ]
):
    server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
    auth_repo: AuthorizationRepository = inject.instance(AuthorizationRepository)
    client = get_client(server_config.server.project, event.client_id)
    user = AuthorizedUser(auth_repo.retrieve_user(user_id=event.user_id))
    if not are_client_permissions_valid(client, user):
        raise ClientPermissionDenied


def check_set_auth_attributes(event: PreSetAuthAttributesEvent):
    if event.mfa_enabled is False:
        user = AuthorizationService().retrieve_user_profile(event.user_id)
        authz_user = AuthorizedUser(user)
        if (
            authz_user.deployment.security
            and authz_user.deployment.security.mfaRequired
        ):
            raise MFARequiredException


def are_client_permissions_valid(client: Client, user: AuthorizedUser):
    # when no role ids set, then all roles are forbidden
    if client.roleIds and user.user_type() in client.roleIds:
        return True
    return False


def get_default_care_plan_group(deployment: Deployment):
    groups_exist = deployment.carePlanGroup and deployment.carePlanGroup.groups
    if not groups_exist:
        return None

    for group in deployment.carePlanGroup.groups:
        if group.default:
            return group


@autoparams("auth_repo")
def mark_auth_user_email_verified(
    user: User, session: ClientSession, auth_repo: AuthRepository
):
    auth_repo.session = session
    auth_repo.confirm_email(uid=user.id, email=user.email)


@autoparams("auth_repo")
def delete_invitation_with_session(
    invitation_id: str, session: ClientSession, auth_repo: AuthorizationRepository
):
    auth_repo.session = session
    auth_repo.delete_invitation_with_session(
        invitation_id=invitation_id, session=session
    )


def _prepare_new_user(user_data: dict, client: Client) -> User:
    session = user_data.pop(PostSignUpEvent.SESSION, None)
    role_id = user_data.pop(RoleAssignment.ROLE_ID, None)
    resource = user_data.pop(RoleAssignment.RESOURCE, None)
    user_data.update(user_data["userAttributes"])
    user_data = remove_none_values(user_data)
    validation_data = user_data.get("validationData", {})
    activation_code = validation_data.pop("activationCode", None)
    invitation_code = validation_data.pop("invitationCode", None)
    shortened_invitation_code = validation_data.pop("shortenedCode", None)
    master_key = validation_data.pop("masterKey", None)

    if not (
        activation_code or master_key or invitation_code or shortened_invitation_code
    ):
        raise ValidationDataError("Activation code is not provided")

    user: User = User.from_dict(user_data)

    if master_key:
        config_key = inject.instance(PhoenixServerConfig).server.project.masterKey
        if master_key != config_key:
            raise WrongActivationOrMasterKeyException
        elif client.clientType == client.ClientType.SERVICE_ACCOUNT:
            user.roles = [RoleAssignment.create_role(role_id, resource)]
        else:
            user.roles = [RoleAssignment.create_super_admin()]
    elif activation_code:
        (
            deployment,
            role,
            care_plan_group_id,
        ) = DeploymentService().retrieve_deployment_with_code(activation_code)
        user.roles = [RoleAssignment.create_role(role, deployment.id)]
        if care_plan_group_id:
            user.carePlanGroupId = care_plan_group_id
    elif invitation_code or shortened_invitation_code:
        if not user.email:
            raise ValidationDataError("Email not provided")
        try:
            invitation = retrieve_invitation(
                invitation_code=invitation_code,
                shortened_invitation_code=shortened_invitation_code,
            )
        except ObjectDoesNotExist:
            raise InvitationDoesNotExistException

        if invitation.email:
            if invitation.email.lower() != user.email.lower():
                raise InvalidRequestException
            # marking email as verified because sign up is based on invitation
            mark_auth_user_email_verified(user, session)
            # will delete the invitation upon successful further user creation
            delete_invitation_with_session(invitation.id, session)
        user.roles = invitation.roles

    return user


def create_tag_log(event: PostCreateTagEvent):
    """Create tag logs in separate collection after user tags were created."""
    AuthorizationService().create_tag_log(TagLog.from_dict(event.to_dict()))


def create_assign_label_logs(event: PostAssignLabelEvent):
    """Create label logs in separate collection after user labels are assigned."""
    label_log_list: list[LabelLog] = []
    if not event.labels:
        return
    for user_id in event.user_ids:
        for label in event.labels:
            label_log_list.append(
                LabelLog.from_dict(
                    {
                        **event.to_dict(),
                        LabelLog.USER_ID: user_id,
                        LabelLog.LABEL_ID: label.id,
                    }
                )
            )
    AuthorizationService().create_assign_label_logs(label_log_list)


def update_recent_module_results(event: PostCreateModuleResultBatchEvent):
    AuthorizationService().update_recent_results(
        [primitive for primitive in (event.primitives or {}).values()]
    )


def update_calendar_on_profile_update(event: PostUserProfileUpdateEvent):
    timezone_update = event.updated_fields.timezone
    if not timezone_update:
        return

    user = event.updated_fields
    previous_state_provided = bool(event.previous_state)
    if previous_state_provided:
        tz_changed = user.timezone != event.previous_state.timezone
        if not tz_changed:
            return

    service = CalendarService()
    service.calculate_and_save_next_day_events_for_user(user.id, user.timezone)


def check_auth_notification(_: NotificationAuthEvent):
    if not g.authz_user.is_super_admin() and request.path.endswith("push"):
        raise UnauthorizedException


def update_user_profile_email(event: PostSetAuthAttributesEvent):
    if not event.email:
        return
    user = extract_user(event.user_id)
    if user.email:
        return
    update_user = UpdateUserProfileRequestObject(id=event.user_id, email=event.email)
    service = AuthorizationService()
    service.update_user_profile(update_user)


def update_user_profile_last_login(event: PostSignInEvent):
    update_user = UpdateUserProfileRequestObject(
        id=event.user_id, lastLoginDateTime=datetime.utcnow()
    )
    service = AuthorizationService()
    service.update_user_profile(update_user)


@autoparams("repo")
def delete_user_role(
    event: DeleteDeploymentCustomRolesEvent,
    repo: AuthorizationRepository,
):
    deleted_ids = set(event.deleted_ids)

    profiles, _ = repo.retrieve_user_profiles(
        deployment_id=event.deployment_id,
        search="",
        role=RoleName.MANAGER,
    )

    service = AuthorizationService()
    for profile in profiles:
        success = profile.remove_roles(deleted_ids, event.deployment_id)
        if success:
            service.update_user_roles(profile.id, profile.roles)


def check_deployment_mfa(event: TokenExtractionEvent):
    service = AuthorizationService()
    user = service.retrieve_user_profile(event.id)
    user = AuthorizedUser(user)
    decoded_token = verify_jwt_in_request()

    if user.deployment.security and user.deployment.security.mfaRequired:
        check_token_valid_for_mfa(decoded_token)


def on_user_delete_callback(event: DeleteUserEvent):
    user_service = AuthorizationService()
    logger.info(
        f"User delete event has been triggered. Deleting user with ID {event.user_id}"
    )
    user_service.delete_user(session=event.session, user_id=event.user_id)


def retrieve_users_timezones(event: RequestUsersTimezonesEvent) -> dict:
    """
    Retrieve timezones by user id.
    @param event: RequestUsersTimezonesEvent event with list if user ids
    @return: dict {userId: timezoneName}
    """
    repo = inject.instance(AuthorizationRepository)
    return repo.retrieve_users_timezones(set(event.ids))


def get_proxy_of_user(user_id: str) -> Optional[str]:
    service = AuthorizationService()
    user = service.retrieve_user_profile(user_id)
    proxies = AuthorizedUser(user).get_assigned_proxies()
    if not proxies:
        return

    proxy_id = next(iter(proxies))[UnlinkProxyRequestObject.PROXY_ID]
    return proxy_id


def off_board_proxy(event: list[PostUnlinkProxyUserEvent, PostUserOffBoardEvent]):
    auth_user = g.authz_user
    req_obj = None
    if isinstance(event, PostUnlinkProxyUserEvent):
        req_obj = {
            OffBoardUserRequestObject.USER_ID: event.user_id,
            OffBoardUserRequestObject.DETAILS_OFF_BOARDED: ReasonDetails.NO_LONGER_NEEDS_MONITORING,
        }
    elif isinstance(event, PostUserOffBoardEvent):
        proxy_id = get_proxy_of_user(event.user_id)
        if proxy_id:
            req_obj = {
                OffBoardUserRequestObject.USER_ID: proxy_id,
                OffBoardUserRequestObject.DETAILS_OFF_BOARDED: event.offboarding_detail,
            }

    if req_obj:
        req_obj.update(
            {
                OffBoardUserRequestObject.SUBMITTER_ID: auth_user.id,
                OffBoardUserRequestObject.DEPLOYMENT: auth_user.deployment,
            }
        )
        req_obj = OffBoardUserRequestObject.from_dict(req_obj)
        OffBoardUserUseCase().execute(req_obj)


def send_user_off_board_push(user_id: str, language: str):
    template = {
        "title": t(f"OffBoardUser.push.title", locale=language),
        "body": t(f"OffBoardUser.push.body", locale=language),
    }
    prepare_and_send_push_notification(
        user_id=user_id, action="OFF_BOARDED", notification_template=template
    )


@autoparams("email_adapter")
def send_user_off_board_notifications(
    event: PostUserOffBoardEvent,
    email_adapter: UserEmailAdapter,
):
    service = AuthorizationService()
    user = service.retrieve_simple_user_profile(user_id=event.user_id)
    send_user_off_board_push(user.id, user.language)

    auth_user = AuthorizedUser(user)
    if user.email:
        email_adapter.send_off_board_user_email(
            user.email, user.language, auth_user.deployment.contactUsURL
        )


def on_change_role_calculate_events(event: PostUserAddRoleEvent):
    if event.new_role == event.old_role:
        return

    service = CalendarService()
    authz_user = event.user
    service.delete_user_events(authz_user.id)
    service.calculate_and_save_next_day_events_for_user(
        authz_user.id, authz_user.user.timezone
    )


def user_add_role_send_email(event: PostUserAddRoleEvent):
    if event.new_role == event.old_role:
        return

    server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
    email_invitation_adapter = inject.instance(EmailInvitationAdapter)
    mail_from = None
    if not event.submitter.is_super_admin():
        mail_from = event.submitter.user.get_full_name()
    mail_to = event.user.user.email
    language = event.user.get_language()
    project = server_config.server.project
    client = project.get_client_by_client_type(Client.ClientType.MANAGER_WEB)
    if event.old_role:
        email_invitation_adapter.send_assign_new_roles_email(
            mail_to, client, language, mail_from, event.new_role, event.old_role
        )
    elif event.resource_name:
        email_invitation_adapter.send_assign_new_multi_resource_role(
            mail_to, client, language, mail_from, event.new_role, event.resource_name
        )


def check_policy_for_generate_token(_: GenerateTokenEvent):
    check_auth()
    IAMBlueprint.check_permissions([get_generate_token_policy()])


def update_user_stats(event: CreateCalendarLogEvent):
    service = AuthorizationService()
    user = service.retrieve_simple_user_profile(user_id=event.user_id)
    stats = UserStatsCalculator(user).run()
    data = {
        UpdateUserProfileRequestObject.ID: user.id,
        UpdateUserProfileRequestObject.STATS: stats,
    }
    req_obj = UpdateUserProfileRequestObject.from_dict(data)
    service.update_user_profile(req_obj)


@autoparams("email_adapter")
def send_user_reactivation_email(
    event: PostUserReactivationEvent, email_adapter: UserEmailAdapter
):
    service = AuthorizationService()
    user = service.retrieve_simple_user_profile(user_id=event.user_id)
    email_adapter.send_reactivate_user_email(
        event.user_id,
        user.email,
        user.givenName,
        user.language,
    )


def assign_organization_owner(event: PostCreateOrganizationEvent):
    service = AuthorizationService()
    user = service.retrieve_simple_user_profile(event.user_id)
    role = AuthorizedUser(user).get_role()
    if role.userType != role.UserType.SUPER_ADMIN:
        return

    if role.id != RoleName.ACCOUNT_MANAGER:
        return

    new_role = RoleAssignment.create_role(
        role_id=RoleName.ORGANIZATION_OWNER,
        resource_id=event.organization_id,
    )
    service.update_user_roles(user.id, [*user.roles, new_role])


def delete_related_role(event: PostDeleteOrganizationEvent):
    service = AuthorizationService()
    user = service.retrieve_simple_user_profile(event.user_id)
    authz_user = AuthorizedUser(user, organization_id=event.organization_id)
    role = authz_user.get_role()
    if not role:
        return

    if role.userType != role.UserType.SUPER_ADMIN:
        return

    roles = user.roles[:]
    roles.remove(authz_user.role_assignment)
    service.update_user_roles(user.id, roles)


@autoparams("repo")
def get_unread_messages_badge(event: GetUserBadgesEvent, repo: InboxRepository):
    unread_count = repo.retrieve_user_unread_messages_count(event.user_id)
    return {"messages": unread_count}
