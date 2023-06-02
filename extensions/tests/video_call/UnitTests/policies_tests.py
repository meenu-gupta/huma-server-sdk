import unittest
from unittest.mock import patch, MagicMock

from flask import Flask, request

from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.twilio_video.router.policies import (
    complete_call_manager_policy,
    complete_call_user_policy,
    initiate_call_policy,
)
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder

PATH = "extensions.twilio_video.router.policies"
AUTHORIZATION_POLICIES_PATH = "extensions.authorization.router.policies"
MANAGER_1 = "5e8f0c74b50aa9656c34789a"
MANAGER_2 = "5e8f0c74b50aa9656c34789b"
USER = "5e8f0c74b50aa9656c34789c"

testapp = Flask(__name__)


def mocked_g():
    gl = MagicMock()
    gl.authz_user = MagicMock(id=MANAGER_2)
    gl.authz_path_user = MagicMock(id=USER)
    return gl


class TwilioPoliciesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.auth_repo = MagicMock()

        def configure_with_binder(binder: Binder):
            binder.bind(AuthorizationRepository, self.auth_repo)

        inject.clear_and_configure(config=configure_with_binder)

    @patch(f"{PATH}.TwilioVideoService")
    def test_complete_call_manager_policy_as_manager(self, twilio_service):
        with testapp.test_request_context():
            video_call_id = manager_id = "some_id"
            video_call = MagicMock()
            video_call.managerId = manager_id
            request.view_args = {
                "video_call_id": video_call_id,
                "manager_id": manager_id,
            }
            twilio_service().retrieve_video_call.return_value = video_call
            try:
                complete_call_manager_policy()
            except PermissionDenied:
                self.fail()

            twilio_service().retrieve_video_call.assert_called_with(
                video_call_id=video_call_id
            )

    @patch(f"{PATH}.TwilioVideoService")
    def test_complete_call_manager_policy_as_another_manager(self, twilio_service):
        with testapp.test_request_context():
            video_call_id = manager_id = "some_id"
            video_call = MagicMock()
            video_call.managerId = manager_id
            request.view_args = {
                "video_call_id": video_call_id,
                "manager_id": "some_other_id",
            }
            twilio_service().retrieve_video_call.return_value = video_call
            with self.assertRaises(PermissionDenied):
                complete_call_manager_policy()

            twilio_service().retrieve_video_call.assert_called_with(
                video_call_id=video_call_id
            )

    @patch(f"{PATH}.TwilioVideoService")
    def test_complete_call_user_policy(self, twilio_service):
        with testapp.test_request_context():
            video_call_id = user_id = "some_id"
            video_call = MagicMock()
            video_call.userId = user_id
            request.view_args = {"video_call_id": video_call_id, "user_id": user_id}
            twilio_service().retrieve_video_call.return_value = video_call
            try:
                complete_call_user_policy()
            except PermissionDenied:
                self.fail()
            twilio_service().retrieve_video_call.assert_called_with(
                video_call_id=video_call_id
            )

    @patch(f"{PATH}.TwilioVideoService")
    def test_complete_call_user_policy_not_allowed_user(self, twilio_service):
        with testapp.test_request_context():
            video_call_id = user_id = "some_id"
            video_call = MagicMock()
            video_call.userId = user_id
            request.view_args = {"video_call_id": video_call_id, "user_id": "other_id"}
            twilio_service().retrieve_video_call.return_value = video_call
            with self.assertRaises(PermissionDenied):
                complete_call_user_policy()
            twilio_service().retrieve_video_call.assert_called_with(
                video_call_id=video_call_id
            )

    @patch(f"{PATH}.g", mocked_g())
    def test_initiate_call_policy__not_for_authz_user_forbidden(self):
        with testapp.test_request_context():
            request.view_args = {"manager_id": MANAGER_1, "user_id": USER}
            with self.assertRaises(PermissionDenied):
                initiate_call_policy()

    @patch(f"{AUTHORIZATION_POLICIES_PATH}.g", mocked_g())
    @patch(f"{PATH}.g", mocked_g())
    @patch(f"{AUTHORIZATION_POLICIES_PATH}.are_users_in_the_same_resource")
    def test_initiate_call_policy__not_for_same_deployment_forbidden(
        self, mocked_same_resource_check
    ):
        with testapp.test_request_context():
            mocked_same_resource_check.return_value = False
            request.view_args = {"manager_id": MANAGER_2, "user_id": USER}
            with self.assertRaises(PermissionDenied):
                initiate_call_policy()
            mocked_same_resource_check.assert_called_once()


if __name__ == "__main__":
    unittest.main()
