import logging
from datetime import datetime
from enum import Enum

from extensions.appointment.exceptions import InvalidDateException
from sdk import meta
from sdk.common.utils.convertible import default_field, convertibleclass
from sdk.common.utils.validators import validate_object_id, default_datetime_meta

logger = logging.getLogger(__name__)


@convertibleclass
class Appointment:
    """Appointment model for scheduling calls with patients"""

    class Status(Enum):
        REJECTED = "REJECTED"
        SCHEDULED = "SCHEDULED"
        PENDING_CONFIRMATION = "PENDING_CONFIRMATION"

        def retrieve_next_statuses(self) -> list:
            if self is self.PENDING_CONFIRMATION:
                return [self.SCHEDULED, self.REJECTED]
            elif self is self.SCHEDULED:
                return [self.REJECTED]
            elif self is self.REJECTED:
                return [self.SCHEDULED]
            return []

    ID = "id"
    USER_ID = "userId"
    TITLE = "title"
    DESCRIPTION = "description"
    MANAGER_ID = "managerId"
    STATUS = "status"
    NOTE_ID = "noteId"
    CALL_ID = "callId"
    START_DATE_TIME = "startDateTime"
    END_DATE_TIME = "endDateTime"
    COMPLETE_DATE_TIME = "completeDateTime"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"
    KEY_ACTION_ID = "keyActionId"

    id: str = default_field(metadata=meta(validate_object_id))
    userId: str = default_field(metadata=meta(validate_object_id))
    title: str = default_field()
    description: str = default_field()

    managerId: str = default_field(metadata=meta(validate_object_id))
    status: Status = default_field()
    noteId: str = default_field(metadata=meta(validate_object_id))
    callId: str = default_field(metadata=meta(validate_object_id))
    keyActionId: str = default_field(metadata=meta(validate_object_id))
    startDateTime: datetime = default_field(metadata=default_datetime_meta())
    endDateTime: datetime = default_field(metadata=default_datetime_meta())
    completeDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())

    def validate_date_times(self):
        now = datetime.utcnow()
        end_date_time = self.endDateTime or self.startDateTime

        if self.startDateTime <= now:
            raise InvalidDateException(f"Schedule appointment for past is prohibited")

        if self.startDateTime > end_date_time:
            raise InvalidDateException(
                "Start of the appointment can't be later than end."
            )
        self.endDateTime = end_date_time

    def is_status_changed(self, old_appointment: "Appointment") -> bool:
        return bool(self.status and self.status != old_appointment.status)

    def is_rescheduled(self, old_appointment: "Appointment") -> bool:
        return bool(
            self.startDateTime and self.startDateTime != old_appointment.startDateTime
        )


class AppointmentAction(Enum):
    CreateAppointment = "CreateAppointment"
    UpdateAppointment = "UpdateAppointment"
    DeleteAppointment = "DeleteAppointment"
    BulkDeleteAppointments = "BulkDeleteAppointments"
