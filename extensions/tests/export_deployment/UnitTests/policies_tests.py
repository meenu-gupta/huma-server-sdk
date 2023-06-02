from unittest import TestCase
from unittest.mock import MagicMock, patch

from flask import Flask

from extensions.export_deployment.router.policies import (
    _check_user_deployment_role_export_permissions,
    get_export_permission,
)
from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
)
from sdk.common.exceptions.exceptions import PermissionDenied, InvalidRequestException

DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
DEPLOYMENT_ID_2 = "5d386cc6ff885918d96edb23"
POLICIES_PATH = "extensions.export_deployment.router.policies"

testapp = Flask(__name__)
testapp.app_context().push()


class ExportPoliciesTestCase(TestCase):
    def get_authz_user(self, deployment_id: str):
        authz_user = MagicMock()
        authz_user.deployment_ids.return_value = [deployment_id]
        return authz_user

    @patch(f"{POLICIES_PATH}._check_deployment_roles_has_export_permission")
    def test_check_user_deployment_role_export_permissions_wildcard(self, next_check):
        authz_user = self.get_authz_user(deployment_id="*")
        _check_user_deployment_role_export_permissions(authz_user, [DEPLOYMENT_ID])
        next_check.assert_called_once()

    @patch(f"{POLICIES_PATH}._check_deployment_roles_has_export_permission")
    def test_success_check_user_deployment_role_export_permissions(self, next_check):
        authz_user = self.get_authz_user(deployment_id=DEPLOYMENT_ID)
        _check_user_deployment_role_export_permissions(authz_user, [DEPLOYMENT_ID])
        next_check.assert_called_once()

    def test_failure_check_user_deployment_role_export_permissions(self):
        authz_user = self.get_authz_user(deployment_id=DEPLOYMENT_ID)
        deployments_to_export = [DEPLOYMENT_ID, DEPLOYMENT_ID_2]
        with self.assertRaises(PermissionDenied):
            _check_user_deployment_role_export_permissions(
                authz_user, deployments_to_export
            )

    @patch(
        f"{POLICIES_PATH}._check_user_deployment_role_export_permissions",
        MagicMock(return_value=True),
    )
    @patch(f"{POLICIES_PATH}.g")
    def test_success_get_export_permission__dict_payload(self, g):
        g.authz_user = self.get_authz_user(deployment_id=DEPLOYMENT_ID)
        sample_payload = {ExportRequestObject.DEPLOYMENT_ID: DEPLOYMENT_ID}
        with testapp.test_request_context("/", method="POST", json=sample_payload) as _:
            try:
                get_export_permission()
            except InvalidRequestException:
                self.fail()

    @patch(f"{POLICIES_PATH}.g")
    def test_failure_get_export_permission__list_payload(self, g):
        g.authz_user = self.get_authz_user(deployment_id=DEPLOYMENT_ID)
        with testapp.test_request_context("/", method="POST", json=[]) as _:
            with self.assertRaises(InvalidRequestException):
                get_export_permission()
