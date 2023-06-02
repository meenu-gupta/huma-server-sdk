from unittest import TestCase
from unittest.mock import MagicMock, patch

from flask import Flask, g

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.key_action.router.policies import get_write_events_policy
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.utils import inject

KEY_ACTION_POLICIES_PATH = "extensions.key_action.router.policies"


class KeyActionsPoliciesTestCase(TestCase):
    def setUp(self) -> None:
        self.auth_repo = MagicMock()
        self.testapp = Flask(__name__)

        def bind(binder):
            binder.bind_to_provider(AuthorizationRepository, lambda: self.auth_repo)

        inject.clear_and_configure(bind)

    def test_get_write_events_policy_when_is_self_request(self):
        with self.testapp.test_request_context():
            g.authz_user = g.authz_path_user = MagicMock()
            policy = get_write_events_policy()
            self.assertEqual(PolicyType.EDIT_OWN_EVENTS, policy)

    @patch(f"{KEY_ACTION_POLICIES_PATH}.is_self_request", MagicMock(return_value=False))
    def test_get_write_events_policy_when_not_proxy_and_not_is_self_request(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_user.is_proxy_for_user.return_value = False
            g.authz_path_user = MagicMock()
            with self.assertRaises(PermissionDenied):
                get_write_events_policy()

    @patch(f"{KEY_ACTION_POLICIES_PATH}.is_self_request", MagicMock(return_value=False))
    @patch(
        f"{KEY_ACTION_POLICIES_PATH}.submitter_and_target_have_same_resource",
        MagicMock(return_value=True),
    )
    def test_get_write_events_policy_when_same_resource(self):
        with self.testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_user.is_proxy_for_user.return_value = False
            g.authz_path_user = MagicMock()
            policy = get_write_events_policy()
            self.assertEqual(PolicyType.EDIT_PATIENT_EVENTS, policy)
