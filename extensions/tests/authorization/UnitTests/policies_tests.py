from unittest import TestCase
from unittest.mock import MagicMock, patch

from flask import Flask, g, request

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import RoleAssignment
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.invitation_request_objects import (
    SendInvitationsRequestObject,
    RetrieveInvitationsRequestObject,
)
from extensions.authorization.router.policies import (
    retrieve_proxy,
    get_invitations_policy,
    get_delete_invitation_policy,
    get_list_invitations_policy,
    get_assign_roles_policy,
    get_retrieve_profile_policy,
    get_assign_proxy_policy,
    deny_user_with_star_resource,
)
from extensions.authorization.router.user_profile_request import LinkProxyRequestObject
from extensions.exceptions import UserDoesNotExist
from sdk.common.exceptions.exceptions import DetailedException, PermissionDenied
from sdk.common.utils import inject

POLICIES_PATH = "extensions.authorization.router.policies"
COMMON_POLICIES_PATH = "extensions.common.policies"
USER_ID_1 = "5e8f0c74b50aa9656c34789a"
USER_ID_2 = "5e84b0dab8dfa268b1180536"
DEPLOYMENT_ID = "5e8f0c74b50aa9656c34789c"
TEST_EMAIL = "proxy@gmail.com"


class MockInvitation:
    def __init__(self, role_id):
        self.role_id = role_id

    instance = MagicMock()
    roles = MagicMock()
    role = MagicMock()


class MockAuthUser:
    instance = MagicMock()
    is_proxy = MagicMock(return_value=False)


class PoliciesTestCase(TestCase):
    def setUp(self) -> None:
        self.auth_repo = MagicMock()
        self.auth_repo.retrieve_user.side_effect = UserDoesNotExist()
        self.testapp = Flask(__name__)

        def bind(binder):
            binder.bind_to_provider(AuthorizationRepository, lambda: self.auth_repo)

        inject.clear_and_configure(bind)

    def test_failure_retrieve_proxy_wrong_email_proper_error_code(self):
        with self.assertRaises(DetailedException) as error:
            retrieve_proxy("wrong@email.com")
            self.assertEqual(300011, error.exception.code)

    def test_get_invitations_policy_for_user(self):
        body = {SendInvitationsRequestObject.ROLE_ID: RoleName.USER}
        with self.testapp.test_request_context(json=body):
            g.authz_user = MagicMock()
            policy = get_invitations_policy()
            self.assertEqual(PolicyType.INVITE_PATIENTS, policy)

    def test_get_invitations_policy_for_proxy(self):
        body = {SendInvitationsRequestObject.ROLE_ID: RoleName.PROXY}
        with self.testapp.test_request_context(json=body):
            g.authz_user = MagicMock()
            policy = get_invitations_policy()
            self.assertEqual(PolicyType.INVITE_PROXY_FOR_PATIENT, policy)

    def test_get_invitations_policy_for_other_roles(self):
        body = {}
        with self.testapp.test_request_context(json=body):
            g.authz_user = MagicMock()
            policy = get_invitations_policy()
            self.assertEqual(PolicyType.INVITE_STAFFS, policy)

    @patch(f"{POLICIES_PATH}.invitation_has_same_resource_as_submitter")
    @patch(f"{POLICIES_PATH}.InvitationRepository")
    def test_get_delete_invitation_policy_when_resource_is_same(
        self, invitation_repo, is_same_resource
    ):
        is_same_resource.return_value = True
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            request.view_args = MagicMock()
            policy = get_delete_invitation_policy(invitation_repo)
            self.assertEqual(PolicyType.INVITE_STAFFS, policy)

    @patch(f"{POLICIES_PATH}.invitation_has_same_resource_as_submitter")
    @patch(f"{POLICIES_PATH}.InvitationRepository")
    def test_get_delete_invitation_policy_when_resource_not_same(
        self, invitation_repo, is_same_resource
    ):
        is_same_resource.return_value = False
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            request.view_args = MagicMock()
            with self.assertRaises(PermissionDenied):
                get_delete_invitation_policy(invitation_repo)

    @patch(f"{POLICIES_PATH}.InvitationRepository")
    def test_get_delete_invitation_policy_for_user(self, invitation_repo):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            request.view_args = MagicMock()
            invitation_repo.retrieve_invitation.return_value = MockInvitation(
                RoleName.USER
            )
            policy = get_delete_invitation_policy(invitation_repo)
            self.assertEqual(PolicyType.INVITE_PATIENTS, policy)

    @patch(f"{POLICIES_PATH}.InvitationRepository")
    def test_get_delete_invitation_policy_for_proxy(self, invitation_repo):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            request.view_args = MagicMock()
            invitation_repo.retrieve_invitation.return_value = MockInvitation(
                RoleName.PROXY
            )
            policy = get_delete_invitation_policy(invitation_repo)
            self.assertEqual(PolicyType.INVITE_PROXY_FOR_PATIENT, policy)

    def test_get_list_invitations_policy_for_user(self):
        body = {
            RetrieveInvitationsRequestObject.ROLE_TYPE: RetrieveInvitationsRequestObject.RoleType.USER.value
        }
        with self.testapp.test_request_context(json=body):
            g.authz_user = MagicMock()
            policy = get_list_invitations_policy()
            self.assertEqual(PolicyType.INVITE_PATIENTS, policy)

    def test_get_list_invitations_policy_for_other_roles(self):
        body = {}
        with self.testapp.test_request_context(json=body):
            g.authz_user = MagicMock()
            policy = get_list_invitations_policy()
            self.assertEqual(PolicyType.INVITE_STAFFS, policy)

    @patch(f"{POLICIES_PATH}.is_self_request", MagicMock(return_value=True))
    def test_get_assign_roles_policy_when_is_self_request(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            policy = get_assign_roles_policy()
            self.assertEqual(PolicyType.ASSIGN_ROLES_TO_STAFF, policy)

    @patch(f"{POLICIES_PATH}.invitation_has_same_resource_as_submitter")
    def test_get_assign_roles_policy_when_not_same_resource(self, is_same_resource):
        is_same_resource.return_value = False
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            with self.assertRaises(PermissionDenied):
                get_assign_roles_policy()

    @patch(f"{COMMON_POLICIES_PATH}.is_self_request", MagicMock(return_value=True))
    def test_get_retrieve_profile_policy_when_is_self_request(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            g.authz_path_user.is_proxy_for_user.return_value = False
            policy = get_retrieve_profile_policy()
            self.assertEqual(PolicyType.VIEW_OWN_PROFILE, policy)

    def test_get_retrieve_profile_policy_for_proxy(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            policy = get_retrieve_profile_policy()
            self.assertEqual(PolicyType.VIEW_PROXY_PROFILE, policy)

    @patch(f"{COMMON_POLICIES_PATH}.is_self_request", MagicMock(return_value=False))
    def test_get_retrieve_profile_policy_if_not_proxy_and_self_request(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            g.authz_path_user.is_proxy_for_user.return_value = False
            with self.assertRaises(PermissionDenied):
                get_retrieve_profile_policy()

    @patch(f"{POLICIES_PATH}.AuthorizedUser", MagicMock())
    @patch(f"{POLICIES_PATH}.retrieve_proxy", MagicMock())
    def test_get_assign_proxy_policy(self):
        body = {LinkProxyRequestObject.PROXY_EMAIL: TEST_EMAIL}
        with self.testapp.test_request_context(json=body):
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            policy = get_assign_proxy_policy()
            self.assertEqual(PolicyType.EDIT_OWN_PROFILE, policy)

    @patch(f"{POLICIES_PATH}.AuthorizedUser", MagicMock())
    @patch(f"{POLICIES_PATH}.retrieve_proxy", MagicMock())
    def test_get_assign_proxy_policy_when_user_and_proxy_email_same(self):
        body = {LinkProxyRequestObject.PROXY_EMAIL: TEST_EMAIL}
        with self.testapp.test_request_context(json=body):
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            g.authz_path_user.user.email = TEST_EMAIL
            with self.assertRaises(PermissionDenied):
                get_assign_proxy_policy()

    @patch(f"{POLICIES_PATH}.AuthorizedUser")
    @patch(f"{POLICIES_PATH}.retrieve_proxy", MagicMock())
    def test_get_assign_proxy_policy_when_user_is_not_proxy(self, auth_user):
        auth_user.return_value = MockAuthUser()
        body = {LinkProxyRequestObject.PROXY_EMAIL: TEST_EMAIL}
        with self.testapp.test_request_context(json=body):
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            with self.assertRaises(PermissionDenied):
                get_assign_proxy_policy()

    def test_deny_user_with_star_resource(self):
        with self.testapp.test_request_context():
            g.user = MagicMock()
            g.user.roles = [
                RoleAssignment.from_dict(
                    {
                        RoleAssignment.ROLE_ID: RoleName.USER,
                        RoleAssignment.RESOURCE: "deployment/6156ad33a7082b29f6c6d0e8",
                    }
                ),
                RoleAssignment.from_dict(
                    {
                        RoleAssignment.ROLE_ID: RoleName.USER,
                        RoleAssignment.RESOURCE: "/*",
                    }
                ),
            ]
            g.user.roles[0].resource = None
            with self.assertRaises(PermissionDenied):
                deny_user_with_star_resource()
