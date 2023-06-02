import unittest
from unittest.mock import patch, MagicMock

from flask import Flask, g

from extensions.revere.models.revere import RevereTest
from extensions.revere.router.policies import (
    get_read_revere_tests_policy,
    get_write_revere_tests_policy,
)
from sdk.common.exceptions.exceptions import PermissionDenied

PATH = "extensions.revere.router.policies"

testapp = Flask(__name__)


class ReverePoliciesTestCase(unittest.TestCase):
    def test_get_read_revere_policy(self):
        with testapp.test_request_context():
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            try:
                get_read_revere_tests_policy()
            except PermissionDenied:
                self.fail()

    @patch(f"{PATH}.is_self_request", MagicMock(return_value=True))
    def test_get_read_revere_not_finished(self):
        body = {RevereTest.STATUS: RevereTest.Status.STARTED.value}
        with testapp.test_request_context(json=body):
            g.authz_user = MagicMock()
            g.authz_path_user = MagicMock()
            with self.assertRaises(PermissionDenied):
                get_read_revere_tests_policy()

    @patch(f"{PATH}.is_self_request", MagicMock(return_value=False))
    def test_get_write_revere_tests_policy__not_self_request(self):
        with testapp.test_request_context():
            with self.assertRaises(PermissionDenied):
                get_write_revere_tests_policy()

    @patch(f"{PATH}.get_user_route_write_policy")
    @patch(f"{PATH}.is_self_request", MagicMock(return_value=True))
    def test_get_write_revere_tests_policy__self_request(
        self, get_user_route_write_policy
    ):
        with testapp.test_request_context():
            get_write_revere_tests_policy()
            get_user_route_write_policy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
