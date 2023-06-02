import logging
import traceback
from dataclasses import dataclass
from datetime import datetime

from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
)
from sdk.common.utils.convertible import default_field, meta
from sdk.common.utils.validators import (
    remove_none_values,
    default_datetime_meta,
    validate_object_id,
)

logger = logging.getLogger(__name__)


@dataclass
class AppointmentEvent(CalendarEvent):
    APPOINTMENT_DATE_TIME = "appointmentDateTime"
    APPOINTMENT_ID = "appointmentId"
    APPOINTMENT_STATUS = "appointmentStatus"
    EXTRA_FIELD_NAMES = (APPOINTMENT_DATE_TIME, APPOINTMENT_ID, APPOINTMENT_STATUS)

    appointmentDateTime: datetime = default_field(metadata=default_datetime_meta())
    appointmentStatus: str = default_field()
    appointmentId: str = default_field(metadata=meta(validate_object_id))

    def execute(self, run_async=True):
        action = "APPOINTMENT_OPEN_MODULE"
        logger.debug(f"Sending appointment notification for #{self.userId}")
        notification_template = {"title": self.title, "body": self.description}
        try:
            prepare_and_send_push_notification(
                self.userId, action, notification_template, run_async=run_async
            )
        except Exception as error:
            logger.warning(
                f"Error sending appointment notification to #{self.userId}: {error}. "
                f"Details: {traceback.format_exc()}"
            )

    def pack_extra_fields(self):
        extra_fields = {}
        for field_name in self.EXTRA_FIELD_NAMES:
            value = getattr(self, field_name, None)
            extra_fields[field_name] = value
            setattr(self, field_name, None)
        self.extraFields = remove_none_values(extra_fields)
