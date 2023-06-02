import unittest
from pathlib import Path
from unittest.mock import patch

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.reminder.component import UserModuleReminderComponent
from extensions.reminder.models.reminder import UserModuleReminder
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.calendar.tasks import prepare_events_for_next_day
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.utils.convertible import ConvertibleClassValidationError

VALID_USER_ID = "5e84b0dab8dfa268b1180536"
INVALID_USER_ID = "6e84b0dab8dfa268b1180532"

VALID_MANAGER_ID = "5e8f0c74b50aa9656c34789c"

VALID_REMINDER_ID = "5e8cc88d0e8f49bbe59d11bd"
INVALID_REMINDER_ID = "2e8cc88d0e8f49bbe59d11ba"

DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"


def sample_reminder() -> dict:
    return {
        "durationIso": "PT20H40M",
        "enabled": True,
        "userId": VALID_USER_ID,
        "moduleName": "BloodPressure",
        "moduleId": "BloodPressure",
        "moduleConfigId": "608089adc97ce231cb445eb4",
    }


def sample_daily_reminder() -> dict:
    base = sample_reminder()
    base["specificWeekDays"] = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    return base


def sample_monthly_reminder() -> dict:
    base = sample_reminder()
    base["specificMonthDays"] = [3, 10]
    return base


def sample_weekly_reminder() -> dict:
    base = sample_reminder()
    base["specificWeekDays"] = ["MON"]
    return base


class BaseReminderTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        CalendarComponent(),
        UserModuleReminderComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/reminders_dump.json")]

    def setUp(self):
        super().setUp()

        self.headers = self.get_headers_for("User")
        self.base_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}/reminder"

    def get_headers_for(self, role: str = "Admin"):
        user_id = VALID_MANAGER_ID if role == "Admin" else VALID_USER_ID
        return self.get_headers_for_token(user_id)


class CreateReminderTestCase(BaseReminderTestCase):
    def test_create_reminder_for_non_existing_module(self):
        data = sample_daily_reminder()
        data[UserModuleReminder.MODULE_ID] = "I do not exist"
        rsp = self.flask_client.post(
            f"{self.base_route}", json=data, headers=self.headers
        )
        self.assertEqual(400, rsp.status_code)

    def test_valid_create_reminder(self):
        rsp = self.flask_client.post(
            f"{self.base_route}", json=sample_daily_reminder(), headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}", json=sample_monthly_reminder(), headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}", json=sample_weekly_reminder(), headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_set_title_and_description_to_reminder_no_title_and_description(self):
        rsp = self.flask_client.post(
            f"{self.base_route}", json=sample_daily_reminder(), headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_route}/{rsp.json['id']}", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        body = rsp.json
        self.assertEqual(body["description"], "Test BP body")
        self.assertEqual(body["title"], "Test Blood Pressure")

    def test_set_title_and_description_to_reminder_with_title_and_description(self):
        body = sample_daily_reminder()
        body["title"] = "awesome_title"
        body["description"] = "awesome_description"
        rsp = self.flask_client.post(
            f"{self.base_route}", json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_route}/{rsp.json['id']}", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        body = rsp.json
        self.assertEqual(body["description"], "awesome_description")
        self.assertEqual(body["title"], "awesome_title")

    def test_invalid_multiple_type_of_reminder(self):
        weekly_reminder = sample_weekly_reminder()
        weekly_reminder["specificMonthDays"] = [3, 10]

        rsp = self.flask_client.post(
            f"{self.base_route}", json=weekly_reminder, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)

        monthly_reminder = sample_monthly_reminder()
        monthly_reminder["specificWeekDays"] = ["MON"]

        rsp = self.flask_client.post(
            f"{self.base_route}", json=monthly_reminder, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_create_reminder_by_manager(self):
        headers = self.get_headers_for("Admin")
        rsp = self.flask_client.post(
            f"{self.base_route}", json=sample_daily_reminder(), headers=headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_create_reminder_with_title_and_description_from_config(self):
        rsp = self.flask_client.post(
            f"{self.base_route}", json=sample_daily_reminder(), headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_route}/{rsp.json['id']}", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        body = rsp.json
        self.assertEqual(body["description"], "Test BP body")
        self.assertEqual(body["title"], "Test Blood Pressure")

    def test_success_create_reminder_and_change_languauge(self):
        rsp = self.flask_client.post(
            f"{self.base_route}", json=sample_daily_reminder(), headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        headers = {"x-hu-locale": "nl", **self.headers}
        rsp = self.flask_client.get(
            f"{self.base_route}/{rsp.json['id']}", headers=headers
        )
        self.assertEqual(200, rsp.status_code)

        body = rsp.json
        self.assertEqual(body["description"], "Test bloeddruk lichaam")
        self.assertEqual(body["title"], "Bloeddruk testen")

    def test_success_create_reminder_and_change_to_non_translated_language_should_stay_the_same(
        self,
    ):
        rsp = self.flask_client.post(
            f"{self.base_route}", json=sample_daily_reminder(), headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        headers = {"x-hu-locale": "ar", **self.headers}
        rsp = self.flask_client.get(
            f"{self.base_route}/{rsp.json['id']}", headers=headers
        )
        self.assertEqual(200, rsp.status_code)

        body = rsp.json
        self.assertEqual(body["description"], "Test BP body")
        self.assertEqual(body["title"], "Test Blood Pressure")


class UpdateReminderTestCase(BaseReminderTestCase):
    def test_valid_reminder_update(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_REMINDER_ID}",
            json=sample_daily_reminder(),
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

    def test_valid_reminder_update_without_durationIso(self):
        reminder_update_dict = sample_daily_reminder()
        reminder_update_dict.pop(UserModuleReminder.DURATION_ISO)
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_REMINDER_ID}",
            json=reminder_update_dict,
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

    def test_invalid_id_update(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/{INVALID_REMINDER_ID}",
            json=sample_daily_reminder(),
            headers=self.headers,
        )
        self.assertEqual(404, rsp.status_code)

    def test_invalid_type_update(self):
        reminder = sample_weekly_reminder()
        reminder[UserModuleReminder.SPECIFIC_MONTH_DAYS] = [1, 3]
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_REMINDER_ID}",
            json=reminder,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)
        err_msg = (
            f"Only one of {UserModuleReminder.SPECIFIC_WEEK_DAYS},"
            f"{UserModuleReminder.SPECIFIC_MONTH_DAYS} should be present"
        )
        self.assertEqual(err_msg, rsp.json["message"])
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_invalid_month_days_update(self):
        reminder = sample_daily_reminder()
        reminder[UserModuleReminder.SPECIFIC_MONTH_DAYS] = [1, 32]
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_REMINDER_ID}",
            json=reminder,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)
        correct_error = (
            "Values in list are not in range of [1-31]" in rsp.json["message"]
        )
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])
        self.assertEqual(True, correct_error)

    def test_failure_update_reminder_by_manager(self):
        headers = self.get_headers_for("Admin")
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_REMINDER_ID}",
            json=sample_daily_reminder(),
            headers=headers,
        )
        self.assertEqual(403, rsp.status_code)


class DeleteReminderTestCase(BaseReminderTestCase):
    def test_reminder_delete(self):
        rsp = self.flask_client.delete(
            f"{self.base_route}/{VALID_REMINDER_ID}", headers=self.headers
        )
        self.assertEqual(204, rsp.status_code)

    def test_invalid_id_reminder_delete(self):
        rsp = self.flask_client.delete(
            f"{self.base_route}/{INVALID_REMINDER_ID}", headers=self.headers
        )
        self.assertEqual(404, rsp.status_code)

    def test_failure_delete_reminder_by_manager(self):
        headers = self.get_headers_for("Admin")
        rsp = self.flask_client.delete(
            f"{self.base_route}/{VALID_REMINDER_ID}", headers=headers
        )
        self.assertEqual(403, rsp.status_code)


class GetReminderDetailsTestCase(BaseReminderTestCase):
    def test_valid_id_reminder_retrieve(self):
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_REMINDER_ID}", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

    def test_invalid_id_reminder_retrieve(self):
        rsp = self.flask_client.get(
            f"{self.base_route}/{INVALID_REMINDER_ID}", headers=self.headers
        )
        self.assertEqual(404, rsp.status_code)

    def test_failure_create_reminder_by_manager(self):
        headers = self.get_headers_for("Admin")
        rsp = self.flask_client.get(
            f"{self.base_route}/{INVALID_REMINDER_ID}", headers=headers
        )
        self.assertEqual(403, rsp.status_code)


class GetReminderListTestCase(BaseReminderTestCase):
    def test_valid_reminder_list(self):
        rsp = self.flask_client.put(
            f"{self.base_route}/search", json={}, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json))

    @patch("sdk.calendar.service.calendar_service.CalendarService.clear_cached_events")
    def test_success_run_next_day_events_with_invalid_data(
        self, mock_clear_cached_events
    ):
        try:
            prepare_events_for_next_day.apply()
            mock_clear_cached_events.assert_called_once()
        except ConvertibleClassValidationError:
            self.fail()

    def test_correct_filtering(self):
        body = {"enabled": False}

        rsp = self.flask_client.put(
            f"{self.base_route}/search", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json))
        reminder = rsp.json[0]
        self.assertNotIn(UserModuleReminder.EXTRA_FIELDS, reminder)
        enabled_status = reminder[UserModuleReminder.ENABLED]
        self.assertEqual(False, enabled_status)

        body["enabled"] = True
        rsp = self.flask_client.put(
            f"{self.base_route}/search", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json))
        enabled_status = rsp.json[0][UserModuleReminder.ENABLED]
        self.assertEqual(True, enabled_status)

    def test_failure_create_reminder_by_manager(self):
        headers = self.get_headers_for("Admin")
        rsp = self.flask_client.put(
            f"{self.base_route}/search", json={}, headers=headers
        )
        self.assertEqual(403, rsp.status_code)


if __name__ == "__main__":
    unittest.main()
