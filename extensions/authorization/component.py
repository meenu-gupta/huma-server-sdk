import logging
from typing import Optional, Union
from extensions.authorization.repository.auth_repository import AuthorizationRepository

from flask import Blueprint, request

from extensions.authorization.callbacks import (
    allow_ip_callback,
    register_user_with_role,
    on_token_extraction_callback,
    create_tag_log,
    create_assign_label_logs,
    update_calendar_on_profile_update,
    check_auth_notification,
)
from extensions.authorization.callbacks.callbacks import (
    update_recent_module_results,
    on_calendar_view_users_data_callback,
    check_valid_client_used,
    update_user_profile_email,
    delete_user_role,
    check_set_auth_attributes,
    on_user_delete_callback,
    retrieve_users_timezones,
    user_add_role_send_email,
    check_policy_for_generate_token,
    update_user_stats,
    on_change_role_calculate_events,
    send_user_reactivation_email,
    assign_organization_owner,
    send_user_off_board_notifications,
    delete_related_role,
    update_user_profile_last_login,
    get_unread_messages_badge,
    off_board_proxy,
)
from extensions.authorization.di.components import (
    bind_invitation_repository,
    bind_email_invitation_adapter,
    bind_authorization_repository,
    bind_default_roles,
    bind_user_email_adapter,
)
from extensions.authorization.events.get_badges_event import GetUserBadgesEvent
from extensions.authorization.events.get_custom_role_event import (
    GetDeploymentCustomRoleEvent,
    GetOrganizationCustomRoleEvent,
)
from extensions.authorization.events.post_assign_label_event import PostAssignLabelEvent
from extensions.authorization.events.post_create_tag_event import PostCreateTagEvent
from extensions.authorization.events.post_unlink_proxy_user_event import (
    PostUnlinkProxyUserEvent,
)
from extensions.authorization.events.post_user_add_role_event import (
    PostUserAddRoleEvent,
)
from extensions.authorization.events.post_user_off_board_event import (
    PostUserOffBoardEvent,
)
from extensions.authorization.events.post_user_profile_update_event import (
    PostUserProfileUpdateEvent,
)
from extensions.authorization.events.post_user_reactivation_event import (
    PostUserReactivationEvent,
)
from extensions.authorization.events.update_stats_event import UpdateUserStatsEvent
from extensions.authorization.exceptions import AuthorizationErrorCodes
from extensions.authorization.router.admin_invitation_router import (
    api as admin_invitation_router,
)
from extensions.authorization.router.invitation_router import api as invitation_router
from extensions.authorization.router.invitation_router import (
    api_v1 as invitation_router_v1,
)
from extensions.authorization.router.user_profile_router import api, api_v1
from extensions.authorization.router.public_invitation_router import (
    api as public_invitation_router,
)
from extensions.config.config import AuthorizationConfig
from extensions.deployment.callbacks import (
    deployment_custom_role_callback,
    organization_custom_role_callback,
)
from extensions.deployment.events.delete_custom_roles_event import (
    DeleteDeploymentCustomRolesEvent,
)
from extensions.module_result.event_bus.post_create_module_results_batch_event import (
    PostCreateModuleResultBatchEvent,
)
from extensions.organization.events import (
    PostCreateOrganizationEvent,
    PostDeleteOrganizationEvent,
)
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
from sdk.calendar.events import RequestUsersTimezonesEvent, CalendarViewUserDataEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.utils.inject import Binder, autoparams
from sdk.notification.events.auth_events import NotificationAuthEvent
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class AuthorizationComponent(PhoenixBaseComponent):
    config_class = AuthorizationConfig
    tag_name = "authorization"
    tasks = ["extensions.authorization"]
    _ignored_error_codes = (
        AuthorizationErrorCodes.WRONG_ACTIVATION_OR_MASTER_KEY,
        AuthorizationErrorCodes.MAX_LABELS_ASSIGNED,
        ErrorCodes.PHONE_NUMBER_NOT_SET,
        ErrorCodes.INVALID_CLIENT_ID,
        ErrorCodes.INVALID_PROJECT_ID,
    )

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        self._create_indexes()
        events_callbacks = (
            # check permissions for sending push notification request
            (NotificationAuthEvent, check_auth_notification),
            # create extension user on sdk user create
            (PostSignUpEvent, register_user_with_role),
            # add extension user instance to each request (g.user) with jwt token
            (TokenExtractionEvent, on_token_extraction_callback),
            # create tag log after user tag created
            (PostCreateTagEvent, create_tag_log),
            # create label log after user label assigned
            (PostAssignLabelEvent, create_assign_label_logs),
            # save recent module results to user profile
            (PostCreateModuleResultBatchEvent, update_recent_module_results),
            # return user timezones for calendar periodic task
            (RequestUsersTimezonesEvent, retrieve_users_timezones),
            (PostUserProfileUpdateEvent, update_calendar_on_profile_update),
            (CalendarViewUserDataEvent, on_calendar_view_users_data_callback),
            (PostSignInEvent, update_user_profile_last_login),
            # check that app client is allowed for user's role
            (PostSignInEvent, check_valid_client_used),
            (CheckAuthAttributesEvent, check_valid_client_used),
            (PreRequestPasswordResetEvent, check_valid_client_used),
            (PostSetAuthAttributesEvent, update_user_profile_email),
            (DeleteDeploymentCustomRolesEvent, delete_user_role),
            (PreSetAuthAttributesEvent, check_set_auth_attributes),
            (DeleteUserEvent, on_user_delete_callback),
            (PostUserReactivationEvent, send_user_reactivation_email),
            (PostUserOffBoardEvent, send_user_off_board_notifications),
            (PostUserOffBoardEvent, off_board_proxy),
            (PostUnlinkProxyUserEvent, off_board_proxy),
            (PostUserAddRoleEvent, user_add_role_send_email),
            (PostUserAddRoleEvent, on_change_role_calculate_events),
            (GenerateTokenEvent, check_policy_for_generate_token),
            (GetDeploymentCustomRoleEvent, deployment_custom_role_callback),
            (GetOrganizationCustomRoleEvent, organization_custom_role_callback),
            (UpdateUserStatsEvent, update_user_stats),
            (PostCreateOrganizationEvent, assign_organization_owner),
            (PostDeleteOrganizationEvent, delete_related_role),
            (GetUserBadgesEvent, get_unread_messages_badge),
        )
        for event, callback in events_callbacks:
            event_bus.subscribe(event, callback)

        if self.config.checkAdminIpAddress:
            event_bus.subscribe(PreSignUpEvent, allow_ip_callback)
            logger.info("Admin IP address has been enabled")

        super().post_setup()

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_default_roles(binder)
        bind_authorization_repository(binder)
        bind_invitation_repository(binder)
        bind_email_invitation_adapter(binder)
        bind_user_email_adapter(binder)

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return [
            api,
            api_v1,
            invitation_router,
            invitation_router_v1,
            admin_invitation_router,
            public_invitation_router,
        ]

    def _init_auth(self, blueprint: Blueprint):
        @blueprint.before_request
        def _setup_auth():
            # removing auth check for resend request
            resend_request = request.path.endswith("/resend-invitation")
            public_path = request.path.startswith("/api/public/")
            if resend_request or public_path:
                return
            self.default_auth()

    @autoparams()
    def _create_indexes(self, repo: AuthorizationRepository):
        repo.create_indexes()
