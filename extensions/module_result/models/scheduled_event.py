import logging
from dataclasses import field, dataclass

import i18n

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.services.authorization import AuthorizationService
from extensions.module_result.exceptions import InvalidModuleConfiguration
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
)
from sdk.common.utils.convertible import required_field, meta
from sdk.common.utils.validators import (
    not_empty,
    validate_object_id,
    remove_none_values,
)

logger = logging.getLogger(__name__)


@dataclass
class ScheduledEvent(CalendarEvent):
    ACTION = "SCHEDULE_OPEN_MODULE"

    MODULE_ID = "moduleId"
    MODULE_CONFIG_ID = "moduleConfigId"
    EXTRA_FIELD_NAMES = (MODULE_ID, MODULE_CONFIG_ID)

    moduleId: str = required_field(metadata=meta(not_empty))
    moduleConfigId: str = required_field(metadata=meta(validate_object_id))

    def pack_extra_fields(self):
        extra_fields = {}
        for field_name in self.EXTRA_FIELD_NAMES:
            extra_fields[field_name] = getattr(self, field_name, None)
            setattr(self, field_name, None)
        self.extraFields = remove_none_values(extra_fields)

    def execute(self, run_async=True):
        logger.debug(
            f"Sending {self.ACTION} notification for #{self.userId}/#{self.moduleId}"
        )
        if not (self.title and self.description):
            self.set_default_title_and_description()

        notification_template = {"title": self.title, "body": self.description}
        notification_data = {
            "action": self.ACTION,
            "moduleId": self.moduleId,
            "moduleConfigId": self.moduleConfigId,
        }
        prepare_and_send_push_notification(
            user_id=self.userId,
            action=self.ACTION,
            notification_template=notification_template,
            notification_data=remove_none_values(notification_data),
            run_async=run_async,
        )

    def set_default_title_and_description(self, user: AuthorizedUser = None):
        if not user:
            user = AuthorizationService().retrieve_simple_user_profile(self.userId)
            user = AuthorizedUser(user)

        language = user.get_language()
        config = user.deployment.find_module_config(self.moduleId, self.moduleConfigId)
        notification_data = config.notificationData
        if notification_data and notification_data.title and notification_data.body:
            self.title = i18n.t(notification_data.title, locale=language)
            self.description = i18n.t(notification_data.body, locale=language)
        else:
            raise InvalidModuleConfiguration(
                f"{self.moduleId} module: Notification data is missing"
            )
