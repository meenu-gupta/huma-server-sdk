import unittest
from unittest.mock import MagicMock

from extensions.tests.shared.test_helpers import get_server_project
from sdk.auth.events.set_auth_attributes_events import PreRequestPasswordResetEvent
from sdk.auth.use_case.auth_request_objects import (
    RequestPasswordResetRequestObject,
    ResetPasswordRequestObject,
)
from sdk.auth.use_case.password_reset import (
    RequestPasswordResetUseCase,
    ResetPasswordUseCase,
)
from sdk.tests.auth.UnitTests.base_auth_request_tests import BaseAuthTestCase
from sdk.tests.auth.test_helpers import (
    USER_EMAIL,
    PROJECT_ID,
    TEST_CLIENT_ID,
    USER_ID,
    USER_PASSWORD,
    auth_user,
)


class MockAuthRepo(MagicMock):
    get_user = MagicMock()
    change_password = MagicMock()


class RequestPasswordTestCase(BaseAuthTestCase):
    def setUp(self) -> None:
        self.auth_repo = MagicMock()
        self.auth_repo.get_user().id = USER_ID

        self.config = MagicMock()
        self.config.server.project = get_server_project()
        self.event_bus = MagicMock()

    def test_request_password_reset_calls_event(self):
        use_case = RequestPasswordResetUseCase(
            self.auth_repo, self.config, MagicMock(), self.event_bus
        )
        data = {
            RequestPasswordResetRequestObject.EMAIL: USER_EMAIL,
            RequestPasswordResetRequestObject.CLIENT_ID: TEST_CLIENT_ID,
            RequestPasswordResetRequestObject.PROJECT_ID: PROJECT_ID,
        }
        request_data = RequestPasswordResetRequestObject.from_dict(data)
        use_case.execute(request_data)
        self.event_bus.emit.assert_called_once()
        sent_event = self.event_bus.emit.call_args_list[0].args[0]
        self.assertIsInstance(sent_event, PreRequestPasswordResetEvent)
        self.assertEqual(USER_ID, sent_event.user_id)
        self.assertEqual(TEST_CLIENT_ID, sent_event.client_id)
        self.assertEqual(PROJECT_ID, sent_event.project_id)


class TestResetPasswordUseCase(unittest.TestCase):
    def setUp(self) -> None:
        self.auth_repo = MockAuthRepo()
        self.auth_repo.get_user.return_value = auth_user()

        self.config = MagicMock()
        self.config.server.project = get_server_project()
        self.event_bus = MagicMock()

    def test_password_reset_first_time(self):
        use_case = ResetPasswordUseCase(
            self.auth_repo, self.config, MagicMock(), self.event_bus
        )
        data = {
            ResetPasswordRequestObject.EMAIL: USER_EMAIL,
            ResetPasswordRequestObject.CODE: "NOT_EMPTY",
            ResetPasswordRequestObject.NEW_PASSWORD: USER_PASSWORD,
        }
        request_data = ResetPasswordRequestObject.from_dict(data)
        use_case.execute(request_data)
        self.auth_repo.change_password.assert_called_once()
        call_args = self.auth_repo.change_password.call_args.kwargs
        self.assertEqual(
            data[ResetPasswordRequestObject.EMAIL],
            call_args[ResetPasswordRequestObject.EMAIL],
        )
        self.assertEqual([], call_args["previous_passwords"])
