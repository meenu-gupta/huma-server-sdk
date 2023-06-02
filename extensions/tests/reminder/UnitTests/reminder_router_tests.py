import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.reminder.models.reminder import UserModuleReminder
from extensions.reminder.router.reminder_requests import (
    UpdateUserModuleReminderRequestObject,
)
from extensions.reminder.router.user_module_reminder_router import (
    delete_own_reminder,
    update_module_reminder_for_user,
    retrieve_module_reminders,
    retrieve_module_reminder_for_user,
    create_module_reminder_for_user,
)
from sdk.phoenix.audit_logger import AuditLog

REMINDER_ROUTER_PATH = "extensions.reminder.router.user_module_reminder_router"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{REMINDER_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch.object(AuditLog, "create_log", MagicMock())
class ReminderRouterTestCase(unittest.TestCase):
    @patch(f"{REMINDER_ROUTER_PATH}.CalendarService")
    @patch(f"{REMINDER_ROUTER_PATH}.DeleteReminderRequestObject")
    def test_success_delete_own_reminder(self, req_obj, service):
        user_id = SAMPLE_ID
        reminder_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_own_reminder(user_id, reminder_id)
            req_obj.from_dict.assert_called_with({req_obj.REMINDER_ID: reminder_id})
            service().delete_calendar_event.assert_called_with(
                req_obj.from_dict().reminderId
            )

    @patch(f"{REMINDER_ROUTER_PATH}.jsonify")
    @patch(f"{REMINDER_ROUTER_PATH}.CalendarService")
    @patch(f"{REMINDER_ROUTER_PATH}.UpdateUserModuleReminderRequestObject")
    @patch(f"{REMINDER_ROUTER_PATH}.g")
    def test_success_update_module_reminder_for_user(
        self, g_mock, req_obj, calendar_service, jsonify
    ):
        user_id = SAMPLE_ID
        reminder_id = SAMPLE_ID
        g_mock.path_user.timezone = "UTC"
        payload = {"a": "b"}
        module_id = "moduleId"
        with testapp.test_request_context("/", method="POST", json=payload) as _:

            class MockOldCalendarEvent:
                moduleId = module_id

            calendar_service().retrieve_calendar_event = MagicMock(
                return_value=MockOldCalendarEvent()
            )
            update_module_reminder_for_user(user_id, reminder_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.USER_ID: user_id,
                    req_obj.MODEL: UserModuleReminder.__name__,
                    req_obj.OLD_REMINDER_MODULE_ID: calendar_service()
                    .retrieve_calendar_event()
                    .moduleId,
                }
            )
            calendar_service().update_calendar_event.assert_called_with(
                reminder_id, req_obj.from_dict(), g_mock.path_user.timezone
            )
            jsonify.assert_called_with({"id": reminder_id})

    @patch(f"{REMINDER_ROUTER_PATH}.jsonify")
    @patch(f"{REMINDER_ROUTER_PATH}.CalendarService")
    @patch(f"{REMINDER_ROUTER_PATH}.RetrieveRemindersRequestObject")
    def test_success_retrieve_module_reminders(self, req_obj, service, jsonify):
        user_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            retrieve_module_reminders(user_id)
            req_obj.from_dict.assert_called_with(payload)
            kwargs = {
                f"{UserModuleReminder.EXTRA_FIELDS}.{UserModuleReminder.MODULE_ID}": req_obj.from_dict().moduleId,
                f"{UserModuleReminder.EXTRA_FIELDS}.{UserModuleReminder.MODULE_CONFIG_ID}": req_obj.from_dict().moduleConfigId,
            }
            service().retrieve_raw_events.assert_called_with(
                enabled=req_obj.from_dict().enabled,
                userId=user_id,
                model=UserModuleReminder.__name__,
                **kwargs,
            )
            jsonify.assert_called_with([])

    @patch(f"{REMINDER_ROUTER_PATH}.jsonify")
    @patch(f"{REMINDER_ROUTER_PATH}.CalendarService")
    @patch(f"{REMINDER_ROUTER_PATH}.RetrieveAppointmentRequestObject")
    def test_success_retrieve_module_reminder_for_user(self, req_obj, service, jsonify):
        user_id = SAMPLE_ID
        reminder_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_module_reminder_for_user(user_id, reminder_id)
            req_obj.from_dict.assert_called_with({"appointmentId": reminder_id})
            service().retrieve_calendar_event.assert_called_with(
                req_obj.from_dict().appointmentId,
            )
            jsonify.assert_called_with(service().retrieve_calendar_event().to_dict())

    @patch(f"{REMINDER_ROUTER_PATH}.jsonify")
    @patch(f"{REMINDER_ROUTER_PATH}.CalendarService")
    @patch(f"{REMINDER_ROUTER_PATH}.CreateUserModuleReminderRequestObject")
    @patch(f"{REMINDER_ROUTER_PATH}.g")
    def test_success_create_module_reminder_for_user(
        self, g_mock, req_obj, calendar_service, jsonify
    ):
        tz = "UTC"
        lang = "en"
        g_mock.authz_path_user.get_language = MagicMock(return_value=lang)
        g_mock.authz_path_user.user.timezone = "UTC"
        user_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_module_reminder_for_user(user_id)
            expected_data = {
                **payload,
                req_obj.LANGUAGE: lang,
                req_obj.MODEL: UserModuleReminder.__name__,
                req_obj.USER_ID: user_id,
                req_obj.DEPLOYMENT: g_mock.authz_path_user.deployment,
            }
            req_obj.from_dict.assert_called_with(expected_data)
            calendar_service().create_calendar_event.assert_called_with(
                req_obj.from_dict(), tz
            )
            jsonify.assert_called_with(
                {"id": calendar_service().create_calendar_event()}
            )


if __name__ == "__main__":
    unittest.main()
