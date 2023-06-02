from dataclasses import field
from datetime import datetime, timedelta

import pytz

from extensions.appointment.models.appointment import Appointment
from extensions.authorization.models.authorized_user import AuthorizedUser
from sdk import convertibleclass, meta
from sdk.calendar.models.calendar_event import CalendarEventLog
from sdk.calendar.utils import now_no_seconds
from sdk.common.utils.convertible import (
    ConvertibleClassValidationError,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    must_not_be_present,
    validate_timezone,
    validate_datetime,
    utc_str_val_to_field,
    must_be_present,
    str_to_bool,
    validate_object_id,
)


@convertibleclass
class CreateKeyActionLogRequestObject(CalendarEventLog):
    def as_timezone(self, timezone):
        if self.model == Appointment.__name__:
            return

        tz = pytz.timezone(timezone)
        self.startDateTime = _as_timezone(self.startDateTime, tz)
        self.endDateTime = _as_timezone(self.endDateTime, tz)

    @classmethod
    def validate(cls, action: CalendarEventLog):
        must_not_be_present(
            id=action.id,
            updateDateTime=action.updateDateTime,
            createDateTime=action.createDateTime,
        )


_datetime_meta = meta(validate_datetime, value_to_field=utc_str_val_to_field)


@convertibleclass
class RetrieveKeyActionsRequestObject:
    START = "start"
    END = "end"
    USER_ID = "userId"
    TIMEZONE = "timezone"
    USER = "user"

    user: AuthorizedUser = required_field()

    start: datetime = field(default_factory=now_no_seconds, metadata=_datetime_meta)
    end: datetime = default_field(metadata=_datetime_meta)
    userId: str = required_field(metadata=meta(validate_object_id))
    timezone: str = required_field(metadata=meta(validate_timezone))


@convertibleclass
class RetrieveKeyActionsTimeframeRequestObject(RetrieveKeyActionsRequestObject):
    ALLOW_PAST_EVENTS = "allowPastEvents"

    allowPastEvents: bool = field(
        default=True, metadata=meta(value_to_field=str_to_bool)
    )

    @classmethod
    def validate(cls, instance):
        must_be_present(start=instance.start, end=instance.end)

        if instance.end <= instance.start:
            raise ConvertibleClassValidationError(
                "Field [end] has error [(Timeframe end should be greater than start.)]"
            )


@convertibleclass
class RetrieveExpiringKeyActionsRequestObject(RetrieveKeyActionsRequestObject):
    ONLY_ENABLED = "onlyEnabled"

    end: datetime = field(
        default_factory=lambda: now_no_seconds() + timedelta(hours=48),
        metadata=_datetime_meta,
    )
    onlyEnabled: bool = field(default=True, metadata=meta(value_to_field=str_to_bool))


def _as_timezone(date, tz):
    return date.replace(tzinfo=pytz.UTC).astimezone(tz).replace(tzinfo=None)
