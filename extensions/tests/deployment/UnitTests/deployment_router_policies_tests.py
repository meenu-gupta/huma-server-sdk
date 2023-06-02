import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.deployment.router.policies import match_deployment_or_wildcard
from sdk.common.exceptions.exceptions import PermissionDenied

POLICY_PATH = "extensions.deployment.router.policies"


class MockFlaskRequest:
    instance = MagicMock()
    view_args = {"deployment_id": ""}


app = Flask(__name__)
app.app_context().push()


class DeploymentRouterPoliciesTestCase(unittest.TestCase):
    @patch(f"{POLICY_PATH}.request", MockFlaskRequest)
    @patch(f"{POLICY_PATH}.g")
    def test_deployment_access_policy_no_access(self, mock_g):
        mock_g.authz_user = MagicMock()
        with app.test_request_context("/", method="POST", json={}) as _:
            with self.assertRaises(PermissionDenied):
                match_deployment_or_wildcard()

    @patch(f"{POLICY_PATH}.request", MockFlaskRequest)
    @patch(f"{POLICY_PATH}.g")
    def test_deployment_access_policy_wildcard_access(self, mock_g):
        mock_g.authz_user = MagicMock()
        mock_g.authz_user.role_assignment.resource_id = MagicMock(return_value="*")
        with app.test_request_context("/", method="POST", json={}) as _:
            try:
                match_deployment_or_wildcard()
            except PermissionDenied:
                self.fail()

        MockFlaskRequest().view_args["deployment_id"] = "620cfed9367840eabbaf8ccb"
        with app.test_request_context("/", method="POST", json={}) as _:
            try:
                match_deployment_or_wildcard()
            except PermissionDenied:
                self.fail()

    @patch(f"{POLICY_PATH}.request", MockFlaskRequest)
    @patch(f"{POLICY_PATH}.g")
    def test_deployment_access_policy_has_access(self, mock_g):
        resource_id = "620cfed9367840eabbaf8ccb"
        mock_g.authz_user = MagicMock()
        mock_g.authz_user.role_assignment.resource_id = MagicMock(
            return_value=resource_id
        )
        MockFlaskRequest().view_args["deployment_id"] = resource_id
        with app.test_request_context("/", method="POST", json={}) as _:
            try:
                match_deployment_or_wildcard()
            except PermissionDenied:
                self.fail()
