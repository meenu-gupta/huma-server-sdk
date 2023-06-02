from unittest import TestCase
from unittest.mock import MagicMock, patch

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from extensions.authorization.adapters.user_email_adapter import UserEmailAdapter
from extensions.authorization.models.authorized_user import AuthorizedUser, ProxyStatus
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.authorization.router.user_profile_request import (
    LinkProxyRequestObject,
    UnlinkProxyRequestObject,
)
from extensions.authorization.use_cases.proxy_use_cases import (
    LinkProxyUserUseCase,
    UnlinkProxyUserUseCase,
)
from extensions.exceptions import ProxyAlreadyLinkedException
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.tests.authorization.IntegrationTests.test_helpers import DEPLOYMENT_ID
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.notification.repository.notification_repository import NotificationRepository
from sdk.notification.services.notification_service import NotificationService
from sdk.phoenix.audit_logger import AuditLog
from sdk.tests.auth.test_helpers import USER_ID

PROXY_USER_ID = "5e8f0c74b50aa9656c34789b"
PROXY_USER_EMAIL = "proxy@huma.com"
DEPLOYMENT_RESOURCE = f"deployment/{DEPLOYMENT_ID}"
USER_RESOURCE = f"user/{USER_ID}"


def get_proxy_user(linked=True):
    proxy_linked_role = RoleAssignment(roleId=RoleName.PROXY, resource=USER_RESOURCE)
    proxy_user_roles = [
        RoleAssignment(roleId=RoleName.PROXY, resource=DEPLOYMENT_RESOURCE),
    ]
    if linked:
        proxy_user_roles.append(proxy_linked_role)
    return User(id=PROXY_USER_ID, roles=proxy_user_roles, email=PROXY_USER_EMAIL)


def get_participant_user():
    roles = [RoleAssignment(roleId=RoleName.USER, resource=DEPLOYMENT_RESOURCE)]
    return User(id=USER_ID, roles=roles)


class ProxyUnitTests(TestCase):
    def setUp(self) -> None:
        self.auth_repo = MagicMock()

        self.proxy_user = get_proxy_user()
        self.user = get_participant_user()

        self.auth_repo.retrieve_assigned_to_user_proxies.return_value = [
            self.proxy_user
        ]
        self.auth_repo.retrieve_user_profiles_by_ids.return_value = [
            self.user,
        ]

        def bind_and_configure(binder):
            binder.bind(AuthorizationRepository, self.auth_repo)
            binder.bind(DeploymentRepository, MagicMock())
            binder.bind(ConsentRepository, MagicMock())
            binder.bind(EConsentRepository, MagicMock())

        inject.clear_and_configure(bind_and_configure)

    def test_retrieve_assigned_proxies__returns_none_without_proper_roles(self):
        authz_user = AuthorizedUser(self.user, DEPLOYMENT_ID)
        proxies = authz_user.get_assigned_proxies()
        expected_proxy = {"deploymentId": DEPLOYMENT_ID, "proxyId": PROXY_USER_ID}
        self.assertEqual(len(proxies), 1)
        self.assertEqual(proxies[0], expected_proxy)
        self.assertIsNone(authz_user.get_assigned_participants())

    def test_retrieve_assigned_participant(self):
        self.auth_repo.retrieve_assigned_to_user_proxies.return_value = []
        authz_user = AuthorizedUser(self.proxy_user, DEPLOYMENT_ID)
        participants = authz_user.get_assigned_participants()
        expected_participant = {"deploymentId": DEPLOYMENT_ID, "userId": USER_ID}
        self.assertEqual(1, len(participants))
        self.assertEqual(participants[0], expected_participant)
        self.assertIsNone(authz_user.get_assigned_proxies())

    def test_proxy_linked_status(self):
        authz_user = AuthorizedUser(self.proxy_user)
        self.assertEqual(authz_user.get_proxy_link_status(), ProxyStatus.LINKED)

    def test_proxy_unlinked_status(self):
        unlinked_proxy_user = get_proxy_user(linked=False)
        authz_user = AuthorizedUser(unlinked_proxy_user)
        self.assertEqual(authz_user.get_proxy_link_status(), ProxyStatus.UNLINK)


@patch.object(AuditLog, "create_log", MagicMock())
class ProxyUseCaseTests(TestCase):
    def setUp(self) -> None:
        self.auth_repo = MagicMock()
        self.participant = get_participant_user()
        self.invitation_adapter = MagicMock()

        def bind_and_configure(binder):
            binder.bind(AuthorizationRepository, self.auth_repo)
            binder.bind(DeploymentRepository, MagicMock())
            binder.bind(OrganizationRepository, MagicMock())
            binder.bind(NotificationRepository, MagicMock())
            binder.bind(EmailInvitationAdapter, self.invitation_adapter)
            binder.bind(InvitationRepository, MagicMock())
            binder.bind(UserEmailAdapter, MagicMock())

        inject.clear_and_configure(bind_and_configure)

    def test_link_proxy_use_case__successfully_linked(self):
        proxy_user = get_proxy_user(linked=False)
        self.auth_repo.retrieve_user.side_effect = [proxy_user, self.participant]
        with patch.object(AuthorizedUser, "get_language") as mocked_language:
            mocked_language.return_value = Language.EN
            request_data = {
                LinkProxyRequestObject.AUTHZ_USER: AuthorizedUser(self.participant),
                LinkProxyRequestObject.PROXY_EMAIL: PROXY_USER_EMAIL,
            }
            request_object = LinkProxyRequestObject.from_dict(request_data)
            with patch.object(NotificationService, "push_for_user") as mocked_push:
                use_case = LinkProxyUserUseCase()
                res = use_case.execute(request_object).value
        self.assertEqual(res.proxyId, PROXY_USER_ID)
        mocked_push.assert_called_once()
        notifications_to_send = mocked_push.call_args_list
        self.assertEqual(1, len(notifications_to_send))
        notification = notifications_to_send[0]
        self.assertEqual(PROXY_USER_ID, notification.args[0])

        self.invitation_adapter.send_proxy_role_linked.assert_called_once()
        call_args = self.invitation_adapter.send_proxy_role_linked.call_args_list[0]
        self.assertEqual(PROXY_USER_EMAIL, call_args.kwargs["to"])
        self.assertEqual(Language.EN, call_args.kwargs["locale"])

    def test_link_proxy_use_case__successfully_linked_no_email_not_sent(self):
        """Tests if email notification was not sent when user has no email"""
        proxy_user = get_proxy_user(linked=False)
        proxy_user.email = None
        self.auth_repo.retrieve_user.side_effect = [proxy_user, self.participant]
        with patch.object(AuthorizedUser, "get_language") as mocked_language:
            mocked_language.return_value = Language.EN
            request_data = {
                LinkProxyRequestObject.AUTHZ_USER: AuthorizedUser(self.participant),
                LinkProxyRequestObject.PROXY_EMAIL: PROXY_USER_EMAIL,
            }
            request_object = LinkProxyRequestObject.from_dict(request_data)
            with patch.object(NotificationService, "push_for_user"):
                use_case = LinkProxyUserUseCase()
                use_case.execute(request_object)

        self.invitation_adapter.send_proxy_role_linked.assert_not_called()

    def test_link_proxy_use_case__already_linked_error(self):
        proxy_user = get_proxy_user(linked=True)
        self.auth_repo.retrieve_user.side_effect = [proxy_user, self.participant]
        request_data = {
            LinkProxyRequestObject.AUTHZ_USER: AuthorizedUser(self.participant),
            LinkProxyRequestObject.PROXY_EMAIL: PROXY_USER_EMAIL,
        }
        request_object = LinkProxyRequestObject.from_dict(request_data)
        with self.assertRaises(ProxyAlreadyLinkedException):
            LinkProxyUserUseCase().execute(request_object)

    def test_link_proxy_use_case__not_linked_error_have_another(self):
        unlinked_proxy_user = get_proxy_user(linked=False)
        self.auth_repo.retrieve_user.side_effect = [
            unlinked_proxy_user,
            self.participant,
        ]
        linked_proxy_user = get_proxy_user(linked=True)
        self.auth_repo.retrieve_assigned_to_user_proxies.return_value = [
            linked_proxy_user
        ]
        request_data = {
            LinkProxyRequestObject.AUTHZ_USER: AuthorizedUser(self.participant),
            LinkProxyRequestObject.PROXY_EMAIL: PROXY_USER_EMAIL,
        }
        request_object = LinkProxyRequestObject.from_dict(request_data)
        with self.assertRaises(ProxyAlreadyLinkedException):
            LinkProxyUserUseCase().execute(request_object)

    def test_unlink_proxy_use_case__successfully_unlinked(self):
        proxy_user = get_proxy_user(linked=True)
        self.auth_repo.retrieve_simple_user_profile.return_value = proxy_user
        request_data = {
            UnlinkProxyRequestObject.USER_ID: USER_ID,
            UnlinkProxyRequestObject.PROXY_ID: PROXY_USER_ID,
        }
        request_object = UnlinkProxyRequestObject.from_dict(request_data)
        use_case = UnlinkProxyUserUseCase()
        use_case.execute(request_object)

        # confirming we updating user's roles without proxy role
        update_profile_args = self.auth_repo.update_user_profile.call_args.args
        user_to_update = update_profile_args[0]
        self.assertEqual(len(user_to_update.roles), 1)
        role = user_to_update.roles[0]
        self.assertEqual(role.resource, DEPLOYMENT_RESOURCE)
        self.assertEqual(role.roleId, RoleName.PROXY)
