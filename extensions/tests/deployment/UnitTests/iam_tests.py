from unittest import TestCase
from unittest.mock import patch, MagicMock

from flask import Flask, g

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.deployment.iam.iam import IAMBlueprint
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.utils import inject

IAM_PATH = "extensions.deployment.iam.iam"
app = Flask(__name__)


class IAMBlueprintTestCase(TestCase):
    def setUp(self) -> None:
        inject.clear_and_configure(lambda x: x.bind(DefaultRoles, DefaultRoles()))

    @patch(f"{IAM_PATH}.is_self_request")
    def test_success_require_policy_own_profile(self, mock_is_self):
        blueprint = IAMBlueprint("/test", "test")

        @blueprint.require_policy(PolicyType.VIEW_OWN_PROFILE)
        def test_route():
            pass

        mock_is_self.return_value = True
        test_route()

    @patch(f"{IAM_PATH}.is_self_request")
    def test_success_require_policy_no_policies(self, mock_is_self):
        blueprint = IAMBlueprint("/test", "test")

        @blueprint.require_policy([])
        def test_route():
            pass

        mock_is_self.return_value = False
        test_route()

    @patch(f"{IAM_PATH}.is_self_request")
    def test_failure_require_policy_permission_denied(self, mock_is_self):
        blueprint = IAMBlueprint("/test", "test")

        @blueprint.require_policy(PolicyType.VIEW_PATIENT_PROFILE)
        def test_route():
            pass

        with app.app_context():
            g.authz_user = MagicMock()
            g.authz_user.get_role.return_value = []
            mock_is_self.return_value = False
            with self.assertRaises(PermissionDenied):
                test_route()
