import unittest
from unittest.mock import patch, MagicMock

from extensions.reminder.models.reminder import UserModuleReminder, Weekday
from sdk.common.utils.convertible import ConvertibleClassValidationError

REMINDER_PATH = "extensions.reminder.models.reminder"


def default_reminder():
    return {
        "durationIso": "PT6H13M",
        "enabled": True,
        "userId": "60019625090d076320280736",
        "moduleName": "BloodPressure",
        "moduleId": "BloodPressure",
        "moduleConfigId": "BloodPressure-121-1212",
        "model": "model",
    }


class UserModuleReminderToDictTestCase(unittest.TestCase):
    def test_success_reminder_to_dict(self):
        duration_iso = "P1DT9H2M"
        specific_week_days = [Weekday.MON]
        specific_month_days = [1, 5]
        module_id = "HeartRate"
        module_config_id = "some_config_id"

        reminder = UserModuleReminder(
            durationIso=duration_iso,
            specificWeekDays=specific_week_days,
            specificMonthDays=specific_month_days,
            moduleId=module_id,
            moduleConfigId=module_config_id,
        )
        reminder_dict = reminder.to_dict()
        self.assertEqual(reminder_dict["extraFields"]["durationIso"], "P1DT9H2M")
        self.assertEqual(reminder_dict["extraFields"]["specificMonthDays"], [1, 5])
        self.assertEqual(reminder_dict["extraFields"]["specificWeekDays"], ["MON"])
        self.assertEqual(reminder_dict["extraFields"]["moduleId"], "HeartRate")
        self.assertEqual(
            reminder_dict["extraFields"]["moduleConfigId"], "some_config_id"
        )

    def test_failure_wrong_duration_iso_format(self):
        reminder_dict = default_reminder()
        reminder_dict["durationIso"] = "test1"
        reminder = UserModuleReminder()
        reminder.register("model", UserModuleReminder)
        with self.assertRaises(ConvertibleClassValidationError):
            reminder.from_dict(reminder_dict)

    def test_failure_wrong_specific_month_days(self):
        reminder_dict = default_reminder()
        reminder_dict["specificMonthDays"] = [999, 897]
        reminder = UserModuleReminder()
        reminder.register("model", UserModuleReminder)
        with self.assertRaises(ConvertibleClassValidationError):
            reminder.from_dict(reminder_dict)

    def test_failure_wrong_specific_week_days(self):
        reminder_dict = default_reminder()
        reminder_dict["specificWeekDays"] = ["APRIL"]
        reminder = UserModuleReminder()
        reminder.register("model", UserModuleReminder)
        with self.assertRaises(ConvertibleClassValidationError):
            reminder.from_dict(reminder_dict)

    @patch(f"{REMINDER_PATH}.prepare_and_send_push_notification", MagicMock())
    @patch(f"{REMINDER_PATH}.UserModuleReminder.set_default_title_and_description")
    def test_success_execute_with_title_and_description(self, set_title):
        title = "some_title"
        description = "some_description"
        duration_iso = "P1DT9H2M"
        specific_week_days = [Weekday.MON]
        specific_month_days = [1, 5]
        module_id = "HeartRate"
        module_config_id = "some_config_id"

        UserModuleReminder(
            durationIso=duration_iso,
            specificWeekDays=specific_week_days,
            specificMonthDays=specific_month_days,
            moduleId=module_id,
            moduleConfigId=module_config_id,
            title=title,
            description=description,
        ).execute(run_async=False)
        set_title.assert_not_called()

    @patch(f"{REMINDER_PATH}.AuthorizedUser")
    @patch(f"{REMINDER_PATH}.prepare_and_send_push_notification", MagicMock())
    @patch(f"{REMINDER_PATH}.UserModuleReminder.set_default_title_and_description")
    @patch(f"{REMINDER_PATH}.AuthorizationService")
    def test_success_execute_without_title_and_description(
        self, auth_service, set_title, authz_user
    ):
        duration_iso = "P1DT9H2M"
        specific_week_days = [Weekday.MON]
        specific_month_days = [1, 5]
        module_id = "HeartRate"
        module_config_id = "some_config_id"
        user_id = "611a463797ed5e9bfd8a2ae0"

        UserModuleReminder(
            durationIso=duration_iso,
            specificWeekDays=specific_week_days,
            specificMonthDays=specific_month_days,
            moduleId=module_id,
            moduleConfigId=module_config_id,
            userId=user_id,
        ).execute(run_async=False)
        set_title.assert_called_with(authz_user().get_language())
        auth_service().retrieve_simple_user_profile.assert_called_with(user_id=user_id)

    @patch(f"{REMINDER_PATH}.DeploymentService")
    def test_success_get_config_notification_data(self, deployment_service):
        duration_iso = "P1DT9H2M"
        specific_week_days = [Weekday.MON]
        specific_month_days = [1, 5]
        module_id = "HeartRate"
        module_config_id = "some_config_id"
        user_id = "611a463797ed5e9bfd8a2ae0"
        UserModuleReminder(
            durationIso=duration_iso,
            specificWeekDays=specific_week_days,
            specificMonthDays=specific_month_days,
            moduleId=module_id,
            moduleConfigId=module_config_id,
            userId=user_id,
        ).get_config_notification_data()

        deployment_service().retrieve_module_config.assert_called_with(module_config_id)
