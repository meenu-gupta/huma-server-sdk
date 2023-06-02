from unittest import TestCase
from unittest.mock import MagicMock, patch

from flask import Flask, g

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.policies import get_read_policy
from extensions.common.policies import (
    is_self_request,
    get_user_route_policy,
    check_proxy_permission,
    submitter_and_target_have_same_resource,
    deny_not_self,
    get_off_board_policy,
    get_read_write_policy,
    get_generate_token_policy,
)
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.utils import inject

COMMON_POLICIES_PATH = "extensions.common.policies"
AUTHORIZATION_POLICIES_PATH = "extensions.authorization.router.policies"
DEPLOYMENT_ID = "5e8f0c74b50aa9656c34789c"


class CommonPoliciesTestCase(TestCase):
    def setUp(self) -> None:
        self.auth_repo = MagicMock()
        self.testapp = Flask(__name__)

        def bind(binder):
            binder.bind_to_provider(AuthorizationRepository, lambda: self.auth_repo)

        inject.clear_and_configure(bind)

    def test_if_is_self_request(self):
        with self.testapp.test_request_context():
            g.authz_user = g.authz_path_user = MagicMock()
            self.assertTrue(is_self_request())

    def test_not_is_self_request(self):
        with self.testapp.test_request_context():
            submitter = MagicMock()
            requested_user = MagicMock()
            g.authz_user = submitter
            g.authz_path_user = requested_user
            self.assertFalse(is_self_request())

    @patch(f"{COMMON_POLICIES_PATH}.is_self_request", MagicMock(return_value=True))
    def test_get_user_route_policy(self):
        with self.testapp.test_request_context():
            g.authz_user = g.authz_path_user = MagicMock()
            policy = get_user_route_policy(
                PolicyType.VIEW_OWN_PROFILE, PolicyType.VIEW_PATIENT_PROFILE
            )
            self.assertEqual(PolicyType.VIEW_OWN_PROFILE, policy)

    def test_check_proxy_permission(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            with self.assertRaises(PermissionDenied):
                check_proxy_permission(deployment_id=DEPLOYMENT_ID)

    def test_submitter_and_target_have_same_resource(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            g.authz_user.deployment_ids.return_value = [DEPLOYMENT_ID]
            g.authz_path_user.deployment_id.return_value = DEPLOYMENT_ID
            self.assertTrue(submitter_and_target_have_same_resource())

    def test_submitter_and_target_have_different_resource(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            g.authz_user.deployment_ids.return_value = ["5e8f0c74b50aa9656c34789d"]
            g.authz_path_user.deployment_id.return_value = DEPLOYMENT_ID
            self.assertFalse(submitter_and_target_have_same_resource())

    def test_deny_not_self(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            with self.assertRaises(PermissionDenied):
                deny_not_self()

    @patch(
        f"{COMMON_POLICIES_PATH}.submitter_and_target_have_same_resource",
        MagicMock(return_value=True),
    )
    def test_get_off_board_policy_same_resource(self):
        with self.testapp.test_request_context():
            policy = get_off_board_policy()
            self.assertEqual(PolicyType.OFF_BOARD_PATIENT, policy)

    @patch(
        f"{COMMON_POLICIES_PATH}.submitter_and_target_have_same_resource",
        MagicMock(return_value=False),
    )
    def test_get_off_board_policy_when_not_same_resource(self):
        with self.testapp.test_request_context():
            with self.assertRaises(PermissionDenied):
                get_off_board_policy()

    def test_get_read_write_policy_when_request_method_post(self):
        with self.testapp.test_request_context(method="POST", json={}):
            read_policy = PolicyType.VIEW_PATIENT_DATA
            write_policy = PolicyType.EDIT_PATIENT_DATA
            policy = get_read_write_policy(read_policy, write_policy)
            self.assertEqual(write_policy, policy)

    def test_get_read_write_policy_when_request_method_get(self):
        with self.testapp.test_request_context(method="GET"):
            read_policy = PolicyType.VIEW_PATIENT_DATA
            write_policy = PolicyType.EDIT_PATIENT_DATA
            policy = get_read_write_policy(read_policy, write_policy)
            self.assertEqual(read_policy, policy)

    def test_get_generate_token_policy(self):
        with self.testapp.test_request_context():
            g.authz_user = g.authz_path_user = MagicMock()
            policy = get_generate_token_policy()
            self.assertEqual(PolicyType.GENERATE_AUTH_TOKEN, policy)

    def test_failure_get_generate_token_policy(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            g.authz_user.is_super_admin.return_value = False
            with self.assertRaises(PermissionDenied):
                get_generate_token_policy()

    @patch(
        f"{AUTHORIZATION_POLICIES_PATH}.is_self_request", MagicMock(return_value=True)
    )
    def test_get_read_policy_as_user(self):
        policy = get_read_policy()
        self.assertEqual(PolicyType.VIEW_OWN_EVENTS, policy)

    @patch(
        f"{AUTHORIZATION_POLICIES_PATH}.is_self_request", MagicMock(return_value=False)
    )
    def test_get_read_policy_when_not_self_request(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_user.is_manager.return_value = False
            with self.assertRaises(PermissionDenied):
                get_read_policy()
