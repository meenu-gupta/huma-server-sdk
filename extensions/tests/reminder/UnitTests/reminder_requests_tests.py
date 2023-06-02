import unittest
from unittest.mock import MagicMock

from extensions.deployment.models.deployment import Deployment
from extensions.reminder.router.reminder_requests import (
    CreateUserModuleReminderRequestObject,
    UpdateUserModuleReminderRequestObject,
    RetrieveRemindersRequestObject,
    DeleteReminderRequestObject,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_VALID_OBJ_ID = "60a20766c85cd55b38c99e12"


def _sample_reminder_dict():
    deployment = MagicMock(spec_set=Deployment)
    deployment.find_module_config.return_value = MagicMock()
    return {
        CreateUserModuleReminderRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID,
        CreateUserModuleReminderRequestObject.DURATION_ISO: "PT9H2M",
        CreateUserModuleReminderRequestObject.MODULE_ID: SAMPLE_VALID_OBJ_ID,
        CreateUserModuleReminderRequestObject.MODEL: "model",
        CreateUserModuleReminderRequestObject.MODULE_CONFIG_ID: SAMPLE_VALID_OBJ_ID,
        CreateUserModuleReminderRequestObject.SPECIFIC_WEEK_DAYS: ["MON"],
        CreateUserModuleReminderRequestObject.DEPLOYMENT: deployment,
    }


class CreateUserModuleReminderRequestObjectTestCase(unittest.TestCase):
    def test_success_create_user_module_reminder_req_obj(self):
        try:
            reminder_dict = _sample_reminder_dict()
            CreateUserModuleReminderRequestObject.from_dict(reminder_dict)

        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_missed_required_fields(self):
        required_fields = [
            CreateUserModuleReminderRequestObject.USER_ID,
            CreateUserModuleReminderRequestObject.DURATION_ISO,
            CreateUserModuleReminderRequestObject.MODULE_ID,
            CreateUserModuleReminderRequestObject.MODEL,
            CreateUserModuleReminderRequestObject.MODULE_CONFIG_ID,
            CreateUserModuleReminderRequestObject.SPECIFIC_WEEK_DAYS,
        ]
        for field in required_fields:
            reminder_dict = _sample_reminder_dict()
            reminder_dict.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                CreateUserModuleReminderRequestObject.from_dict(reminder_dict)

    def test_failure_missed_field_value(self):
        reminder_dict = _sample_reminder_dict()
        reminder_dict[CreateUserModuleReminderRequestObject.SPECIFIC_WEEK_DAYS] = []
        with self.assertRaises(ConvertibleClassValidationError):
            CreateUserModuleReminderRequestObject.from_dict(reminder_dict)

        reminder_dict = _sample_reminder_dict()
        reminder_dict[CreateUserModuleReminderRequestObject.SPECIFIC_MONTH_DAYS] = []
        with self.assertRaises(ConvertibleClassValidationError):
            CreateUserModuleReminderRequestObject.from_dict(reminder_dict)


class UpdateUserModuleReminderRequestObjectTestCase(unittest.TestCase):
    def test_success_update_user_module_reminder_req_obj(self):
        try:
            UpdateUserModuleReminderRequestObject.from_dict(
                {
                    UpdateUserModuleReminderRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID,
                    UpdateUserModuleReminderRequestObject.MODEL: "model",
                    UpdateUserModuleReminderRequestObject.MODULE_ID: SAMPLE_VALID_OBJ_ID,
                    UpdateUserModuleReminderRequestObject.MODULE_CONFIG_ID: SAMPLE_VALID_OBJ_ID,
                    UpdateUserModuleReminderRequestObject.DURATION_ISO: "PT10H0M",
                    CreateUserModuleReminderRequestObject.SPECIFIC_WEEK_DAYS: ["MON"],
                    UpdateUserModuleReminderRequestObject.OLD_REMINDER_MODULE_ID: SAMPLE_VALID_OBJ_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_missed_required_fields(self):
        required_fields = [
            CreateUserModuleReminderRequestObject.USER_ID,
            CreateUserModuleReminderRequestObject.DURATION_ISO,
            CreateUserModuleReminderRequestObject.MODULE_ID,
            CreateUserModuleReminderRequestObject.MODEL,
            CreateUserModuleReminderRequestObject.MODULE_CONFIG_ID,
            CreateUserModuleReminderRequestObject.SPECIFIC_WEEK_DAYS,
        ]
        for field in required_fields:
            reminder_dict = _sample_reminder_dict()
            reminder_dict.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                CreateUserModuleReminderRequestObject.from_dict(reminder_dict)

    def test_success_delete_request_object(self):
        try:
            DeleteReminderRequestObject.from_dict(
                {DeleteReminderRequestObject.REMINDER_ID: SAMPLE_VALID_OBJ_ID}
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_update_user_module_reminder_with_not_matching_module_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            UpdateUserModuleReminderRequestObject.from_dict(
                {
                    UpdateUserModuleReminderRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID,
                    UpdateUserModuleReminderRequestObject.MODEL: "model",
                    UpdateUserModuleReminderRequestObject.MODULE_ID: SAMPLE_VALID_OBJ_ID,
                    UpdateUserModuleReminderRequestObject.MODULE_CONFIG_ID: SAMPLE_VALID_OBJ_ID,
                    UpdateUserModuleReminderRequestObject.DURATION_ISO: "PT10H0M",
                    CreateUserModuleReminderRequestObject.SPECIFIC_WEEK_DAYS: ["MON"],
                    UpdateUserModuleReminderRequestObject.OLD_REMINDER_MODULE_ID: "not matching",
                }
            )


class RetrieveRemindersRequestObjectTestCase(unittest.TestCase):
    def test_success_retrieve_reminder_req_obj(self):
        try:
            RetrieveRemindersRequestObject.from_dict(
                {
                    RetrieveRemindersRequestObject.END_DATE_TIME: "2020-01-01T10:00:00Z",
                    RetrieveRemindersRequestObject.ENABLED: True,
                    RetrieveRemindersRequestObject.MODULE_ID: SAMPLE_VALID_OBJ_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()


if __name__ == "__main__":
    unittest.main()
