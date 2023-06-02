import unittest
from unittest.mock import patch, MagicMock

from extensions.authorization.events.post_user_profile_update_event import (
    PostUserProfileUpdateEvent,
)
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment
from extensions.reminder.callbacks.callbacks import (
    update_reminders_language_localization,
)
from extensions.reminder.models.reminder import UserModuleReminder
from sdk.common.localization.utils import Language

CALLBACK_PATH = "extensions.reminder.callbacks.callbacks"


class ReminderCallbacksTestCase(unittest.TestCase):
    @staticmethod
    def _sample_user(language: str = Language.EN) -> User:
        return User.from_dict(
            {
                User.ID: "6163fe728c5fa31e0b09910c",
                User.EMAIL: "test_user_email@huma.com",
                User.LANGUAGE: language,
                User.ROLES: [
                    {
                        RoleAssignment.ROLE_ID: RoleName.USER,
                        RoleAssignment.RESOURCE: "deployment/999",
                    }
                ],
            }
        )

    @patch(f"{CALLBACK_PATH}.CalendarService")
    def test_success_update_reminders_language_localization__no_changes(
        self, calendar_service
    ):
        user = self._sample_user()
        event = PostUserProfileUpdateEvent(updated_fields=user, previous_state=user)
        update_reminders_language_localization(event)
        calendar_service.retrieve_raw_events.assert_not_called()

    @patch(
        "extensions.authorization.models.user.RoleAssignment._set_user_type",
        MagicMock(),
    )
    @patch(f"{CALLBACK_PATH}.CalendarService")
    @patch(f"{CALLBACK_PATH}.DeploymentService", MagicMock())
    def test_success_update_reminders_language_localization(self, calendar_service):
        calendar_event = MagicMock()
        calendar_event.moduleId = "module_id"
        calendar_event.moduleConfigId = "module_config_id"
        calendar_service().retrieve_raw_events.return_value = [calendar_event]
        old_user = self._sample_user()
        updated_user = self._sample_user(Language.FR)
        event = PostUserProfileUpdateEvent(
            updated_fields=updated_user, previous_state=old_user
        )
        update_reminders_language_localization(event)

        calendar_service().retrieve_raw_events.assert_called_with(
            userId=old_user.id, model=UserModuleReminder.__name__
        )
        calendar_service().update_calendar_event.assert_called_with(
            calendar_event.id, calendar_event, None
        )


if __name__ == "__main__":
    unittest.main()
