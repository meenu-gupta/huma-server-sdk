import i18n

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from extensions.authorization.adapters.user_email_adapter import UserEmailAdapter
from extensions.authorization.events.post_unlink_proxy_user_event import (
    PostUnlinkProxyUserEvent,
)
from extensions.authorization.models.action import AuthorizationAction
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import RoleAssignment, BoardingStatus
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.router.user_profile_request import (
    LinkProxyRequestObject,
    UnlinkProxyRequestObject,
)
from extensions.authorization.router.user_profile_response import (
    LinkProxyUserResponseObject,
)
from extensions.authorization.use_cases.base_authorization_use_case import (
    BaseAuthorizationUseCase,
)
from extensions.exceptions import ProxyAlreadyLinkedException
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils import inject
from sdk.phoenix.audit_logger import AuditLog


class LinkProxyUserUseCase(UseCase):
    LINKED_ACTION = "LINKED"

    @inject.autoparams()
    def __init__(
        self,
        repo: AuthorizationRepository,
        invitation_adapter: EmailInvitationAdapter,
        event_bus: EventBusAdapter,
        email_adapter: UserEmailAdapter,
    ):
        self.auth_repo = repo
        self.invitation_adapter = invitation_adapter
        self._event_bus = event_bus
        self._email_adapter = email_adapter

    def process_request(self, request_object: LinkProxyRequestObject):
        proxy_user = self.auth_repo.retrieve_user(email=request_object.proxyEmail)
        authz_proxy_user = AuthorizedUser(proxy_user)
        participant = request_object.authzUser
        self.check_proxy_relations(authz_proxy_user, participant)
        proxy_role = RoleAssignment.create_proxy(participant.id)
        proxy_user.roles.append(proxy_role)
        is_off_boarded = proxy_user.is_off_boarded()
        if is_off_boarded:
            proxy_user.boardingStatus.status = BoardingStatus.Status.ACTIVE
        self.auth_repo.update_user_profile(proxy_user)
        self.send_linked_notification(authz_proxy_user, is_off_boarded)
        if is_off_boarded:
            self._create_audit_log_for_reactivated_proxy(proxy_user.id)
        return LinkProxyUserResponseObject(proxy_user.id)

    @staticmethod
    def check_proxy_relations(
        authz_proxy_user: AuthorizedUser, authz_participant: AuthorizedUser
    ):
        # forbidden if already linked to any user
        if authz_proxy_user.proxy_participant_ids():
            raise ProxyAlreadyLinkedException
        if authz_participant.get_assigned_proxies():
            raise ProxyAlreadyLinkedException

    def send_linked_notification(self, proxy: AuthorizedUser, is_off_boarded: bool):
        locale = proxy.get_language()
        self.send_linked_push(proxy.id, locale)
        self.send_emails(proxy, locale, is_off_boarded)

    def send_linked_push(self, proxy_id: str, locale: str):
        notification_template = self.get_linked_push_template(locale)
        prepare_and_send_push_notification(
            proxy_id, self.LINKED_ACTION, notification_template
        )

    @staticmethod
    def get_linked_push_template(locale):
        return {
            "title": i18n.t("ProxyLinked.push.title", locale=locale),
            "body": i18n.t("ProxyLinked.push.body", locale=locale),
        }

    def send_emails(self, proxy, locale: str, is_off_boarded: bool):
        if not proxy.user.email:
            return
        if is_off_boarded:
            self._email_adapter.send_reactivate_user_email(
                proxy.user.id,
                proxy.user.email,
                proxy.user.givenName,
                locale,
            )
        self.invitation_adapter.send_proxy_role_linked(
            to=proxy.user.email, locale=locale
        )

    @staticmethod
    def _create_audit_log_for_reactivated_proxy(proxy_id: str):
        AuditLog.create_log(
            action=AuthorizationAction.ReactivateUser, user_id=proxy_id, secure=True
        )


class UnlinkProxyUserUseCase(BaseAuthorizationUseCase):
    @inject.autoparams()
    def __init__(
        self, invitation_repo: InvitationRepository, event_bus: EventBusAdapter
    ):
        super(UnlinkProxyUserUseCase, self).__init__()
        self.invitation_repo = invitation_repo
        self._event_bus = event_bus

    def process_request(self, request_object: UnlinkProxyRequestObject):
        self._unlink_proxy_user(request_object.proxyId, request_object.userId)
        self._delete_proxy_invitation()
        self._post_unlink_proxy_user(request_object.proxyId)
        return request_object.proxyId

    def _delete_proxy_invitation(self):
        try:
            invitation = self.invitation_repo.retrieve_proxy_invitation(
                user_id=self.request_object.userId
            )
        except ObjectDoesNotExist:
            return

        self.invitation_repo.delete_invitation(invitation.id)

    def _unlink_proxy_user(self, proxy_id: str, user_id: str):
        proxy_user = self.auth_repo.retrieve_simple_user_profile(user_id=proxy_id)
        role = RoleAssignment.create_proxy(user_id)
        proxy_user.remove_roles([role.roleId], role.resource)
        self.auth_repo.update_user_profile(proxy_user)

    def _post_unlink_proxy_user(self, user_id: str):
        self._event_bus.emit(PostUnlinkProxyUserEvent(user_id), raise_error=True)
