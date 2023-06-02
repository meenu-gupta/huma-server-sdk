from dataclasses import field
from datetime import datetime, timedelta

from extensions.deployment.models.deployment import Deployment
from extensions.module_result.models.module_config import NotificationData
from extensions.reminder.models.reminder import UserModuleReminder
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.localization.utils import Language
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
    ConvertibleClassValidationError,
)
from sdk.common.utils.json_utils import replace_values
from sdk.common.utils.validators import (
    must_not_be_present,
    must_be_present,
    must_be_only_one_of,
    incorrect_language_to_default,
    validate_object_id,
    not_empty,
)


@convertibleclass
class CreateUserModuleReminderRequestObject(UserModuleReminder):
    LANGUAGE = "language"
    DEPLOYMENT = "deployment"

    language: str = field(
        default=Language.EN, metadata=meta(value_to_field=incorrect_language_to_default)
    )
    deployment: Deployment = required_field()

    def post_init(self):
        self._validate_if_deployment_has_configs_for_module(
            self.deployment, self.moduleId, self.moduleConfigId
        )
        self._set_start_date_time()
        self.build_rrule_from_duration_iso()
        self.set_default_title_and_description(self.language)

    @staticmethod
    def _validate_if_deployment_has_configs_for_module(
        deployment: Deployment, module_id: str, module_config_id: str
    ):
        config = deployment.find_module_config(module_id, module_config_id)
        if not config:
            raise InvalidRequestException(
                f"Configs for module id [{module_id}] does not exist"
            )

    def get_config_notification_data(self) -> NotificationData:
        config = self.deployment.find_module_config(self.moduleId, self.moduleConfigId)
        return config and config.notificationData

    def set_default_title_and_description(self, language: str):
        title_and_body: dict = {
            NotificationData.TITLE: self.title,
            NotificationData.BODY: self.description,
        }

        if not all(title_and_body.values()):
            if notification_data := self.get_config_notification_data():
                title_and_body = notification_data.to_dict()

        title_and_body = self._apply_localization(title_and_body)
        if not all(title_and_body.values()):
            if data := self.get_static_reminder_templates(self.language):
                title_and_body = data

        self.title = title_and_body[NotificationData.TITLE]
        self.description = title_and_body[NotificationData.BODY]

    def _apply_localization(self, data: dict) -> dict:
        localizations = self.deployment.get_localization(self.language)
        return replace_values(data, localizations)

    @classmethod
    def validate(cls, reminder):
        must_not_be_present(
            id=reminder.id,
            updateDateTime=reminder.updateDateTime,
            createDateTime=reminder.createDateTime,
        )

        must_be_present(
            userId=reminder.userId,
            durationIso=reminder.durationIso,
            moduleId=reminder.moduleId,
        )

        must_be_only_one_of(
            specificWeekDays=reminder.specificWeekDays,
            specificMonthDays=reminder.specificMonthDays,
        )


@convertibleclass
class UpdateUserModuleReminderRequestObject(UserModuleReminder):
    OLD_REMINDER_MODULE_ID = "oldReminderModuleId"

    oldReminderModuleId: str = required_field(metadata=meta(not_empty))

    def post_init(self):
        self._set_start_date_time()
        if self.durationIso:
            self.build_rrule_from_duration_iso()

    @classmethod
    def validate(cls, reminder):
        if not reminder.startDateTime:
            reminder.startDateTime = datetime.utcnow() + timedelta(seconds=10)
        must_not_be_present(
            id=reminder.id,
            updateDateTime=reminder.updateDateTime,
            createDateTime=reminder.createDateTime,
        )

        must_be_present(userId=reminder.userId)

        must_be_only_one_of(
            specificWeekDays=reminder.specificWeekDays,
            specificMonthDays=reminder.specificMonthDays,
        )

        if reminder.moduleId and reminder.moduleId != reminder.oldReminderModuleId:
            raise ConvertibleClassValidationError(
                f"New moduleId [{reminder.moduleId}] does not match with current moduleId [{reminder.oldReminderModuleId}] "
            )


@convertibleclass
class RetrieveRemindersRequestObject:
    END_DATE_TIME = "endDateTime"
    ENABLED = "enabled"
    MODULE_ID = "moduleId"
    MODULE_CONFIG_ID = "moduleConfigId"

    endDateTime: str = default_field()
    enabled: bool = default_field()
    moduleId: str = default_field()
    moduleConfigId: str = default_field()


@convertibleclass
class DeleteReminderRequestObject:
    REMINDER_ID = "reminderId"

    reminderId: str = required_field(metadata=meta(validate_object_id))
