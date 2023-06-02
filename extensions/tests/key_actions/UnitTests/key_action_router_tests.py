import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.key_action.router.key_action_router import (
    retrieve_key_actions_in_timeframe,
    retrieve_key_actions_for_user,
    create_key_action_log,
)
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject
from sdk.phoenix.audit_logger import AuditLog

KEY_ACTION_ROUTER_PATH = "extensions.key_action.router.key_action_router"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{KEY_ACTION_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch.object(AuditLog, "create_log", MagicMock())
class KeyActionRouterTestCase(unittest.TestCase):
    def setUp(self) -> None:
        def bind(binder):
            binder.bind_to_provider(EventBusAdapter, MagicMock())

        inject.clear_and_configure(bind)

    @patch(f"{KEY_ACTION_ROUTER_PATH}.jsonify")
    @patch(f"{KEY_ACTION_ROUTER_PATH}.RetrieveKeyActionsTimelineUseCase")
    @patch(f"{KEY_ACTION_ROUTER_PATH}.RetrieveKeyActionsTimeframeRequestObject")
    @patch(f"{KEY_ACTION_ROUTER_PATH}.g")
    def test_success_retrieve_key_actions_in_timeframe(
        self, g_mock, req_obj, use_case, jsonify
    ):
        g_mock.authz_user = MagicMock()
        g_mock.user = MagicMock()
        g_mock.user.timezone = "UTC"
        user_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_key_actions_in_timeframe(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    CalendarEvent.USER_ID: SAMPLE_ID,
                    req_obj.TIMEZONE: g_mock.user.timezone,
                    req_obj.USER: g_mock.authz_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().to_list())

    @patch(f"{KEY_ACTION_ROUTER_PATH}.jsonify")
    @patch(f"{KEY_ACTION_ROUTER_PATH}.RetrieveKeyActionsUseCase")
    @patch(f"{KEY_ACTION_ROUTER_PATH}.RetrieveKeyActionsRequestObject")
    @patch(f"{KEY_ACTION_ROUTER_PATH}.g")
    def test_success_retrieve_key_actions_for_user(
        self, g_mock, req_obj, use_case, jsonify
    ):
        g_mock.user = MagicMock()
        g_mock.authz_user = MagicMock()
        g_mock.user.timezone = "UTC"
        user_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_key_actions_for_user(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    CalendarEvent.USER_ID: SAMPLE_ID,
                    req_obj.TIMEZONE: g_mock.user.timezone,
                    req_obj.USER: g_mock.authz_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{KEY_ACTION_ROUTER_PATH}.jsonify")
    @patch(f"{KEY_ACTION_ROUTER_PATH}.CalendarService")
    @patch(f"{KEY_ACTION_ROUTER_PATH}.CreateKeyActionLogRequestObject")
    @patch(f"{KEY_ACTION_ROUTER_PATH}.g")
    def test_success_create_key_action_log(self, g_mock, req_obj, service, jsonify):
        user_id = SAMPLE_ID
        key_action_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_key_action_log(user_id, key_action_id)
            req_obj.from_dict.assert_called_with(
                {**payload, req_obj.PARENT_ID: key_action_id}
            )
            service().create_calendar_event_log.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": service().create_calendar_event_log()})


if __name__ == "__main__":
    unittest.main()
