import unittest
from unittest.mock import MagicMock, patch

from sdk.auth.model.auth_user import AuthIdentifierType
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.use_case.auth_request_objects import SignOutRequestObjectV1
from sdk.auth.use_case.auth_use_cases import SignOutUseCaseV1
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject
from sdk.tests.auth.test_helpers import USER_ID

USE_CASE_PATH = "sdk.auth.use_case.auth_use_cases"


class SignOutUseCaseV1TestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._repo = MagicMock()
        self._event_bus = MagicMock()

        def configure_with_binder(binder: inject.Binder):
            binder.bind(AuthRepository, self._repo)
            binder.bind(EventBusAdapter, self._event_bus)

        inject.clear_and_configure(config=configure_with_binder)

    @patch(f"{USE_CASE_PATH}.SignOutEventV1")
    @patch(f"{USE_CASE_PATH}.DeviceSessionV1")
    def test_sign_out_use_case(self, mock_session, mock_event):
        req_obj = SignOutRequestObjectV1.from_dict(
            {
                SignOutRequestObjectV1.USER_ID: USER_ID,
                SignOutRequestObjectV1.DEVICE_PUSH_ID: "push_id",
                SignOutRequestObjectV1.DEVICE_AGENT: "agent",
                SignOutRequestObjectV1.REFRESH_TOKEN: "refresh_token",
            }
        )
        SignOutUseCaseV1().execute(req_obj)
        mock_session.from_dict.assert_called_with(req_obj.to_dict(include_none=False))
        self._repo.sign_out_device_session_v1.assert_called_with(
            mock_session.from_dict()
        )
        self._repo.set_auth_attributes.assert_not_called()
        mock_event.assert_called_with(
            user_id=USER_ID, device_push_id="push_id", voip_device_push_id=None
        )
        self._event_bus.emit.assert_called_with(mock_event())

    @patch(f"{USE_CASE_PATH}.get_user")
    @patch(f"{USE_CASE_PATH}.SignOutEventV1")
    @patch(f"{USE_CASE_PATH}.DeviceSessionV1")
    def test_sign_out_use_case_with_device_token(
        self, mock_session, mock_event, mock_get_user
    ):
        req_obj = SignOutRequestObjectV1.from_dict(
            {
                SignOutRequestObjectV1.USER_ID: USER_ID,
                SignOutRequestObjectV1.DEVICE_PUSH_ID: "push_id",
                SignOutRequestObjectV1.VOIP_DEVICE_PUSH_ID: "voip_push_id",
                SignOutRequestObjectV1.DEVICE_AGENT: "agent",
                SignOutRequestObjectV1.DEVICE_TOKEN: "token",
                SignOutRequestObjectV1.REFRESH_TOKEN: "refresh_token",
            }
        )
        SignOutUseCaseV1().execute(req_obj)

        mock_session.from_dict.assert_called_with(req_obj.to_dict(include_none=False))
        self._repo.sign_out_device_session_v1.assert_called_with(
            mock_session.from_dict()
        )

        mock_get_user.assert_called_with(self._repo, uid=USER_ID)
        mock_get_user().remove_mfa_identifier.assert_called_with(
            AuthIdentifierType.DEVICE_TOKEN, "token"
        )

        self._repo.set_auth_attributes.assert_called_with(
            uid=USER_ID, mfa_identifiers=mock_get_user().to_dict().__getitem__()
        )

        mock_event.assert_called_with(
            user_id=USER_ID,
            device_push_id="push_id",
            voip_device_push_id="voip_push_id",
        )
        self._event_bus.emit.assert_called_with(mock_event())
