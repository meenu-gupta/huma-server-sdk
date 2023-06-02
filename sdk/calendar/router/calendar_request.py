from dataclasses import field
from datetime import datetime

from dateutil.relativedelta import relativedelta

from sdk import convertibleclass, meta
from sdk.calendar.utils import now_no_seconds, get_dt_from_str
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    validate_timezone,
    validate_object_id,
)


@convertibleclass
class ExportCalendarRequestObject:
    START = "start"
    END = "end"
    USER_ID = "userId"
    TIMEZONE = "timezone"

    timezone: str = field(default="UTC", metadata=meta(validate_timezone))
    userId: str = required_field(metadata=meta(validate_object_id))
    start: datetime = default_field(metadata=meta(value_to_field=get_dt_from_str))
    end: datetime = default_field(metadata=meta(value_to_field=get_dt_from_str))
    debug: str = default_field()

    def post_init(self):
        now = now_no_seconds()
        self.start = self.start or now - relativedelta(years=1)
        self.end = self.end or now + relativedelta(years=10)
