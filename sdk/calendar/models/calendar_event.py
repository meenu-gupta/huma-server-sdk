from copy import deepcopy
from dataclasses import field, dataclass
from datetime import datetime

import pytz

from sdk import convertibleclass, meta
from sdk.calendar.utils import get_dt_from_str
from sdk.common.exceptions.exceptions import ClassNotRegisteredException
from sdk.common.utils.convertible import (
    to_dict,
    from_dict,
    required_field,
    default_field,
)
from sdk.common.utils.date_utils import rrule_replace_timezone
from sdk.common.utils.validators import (
    validate_id,
    validate_duration,
    default_datetime_meta,
    validate_object_id,
    validate_datetime,
)

_cls = {}


@dataclass
class CalendarEvent:
    DEFAULT_INSTANCE_EXPIRATION_DURATION = "P1W"
    MODULE_ID = "moduleId"

    ID = "id"
    ID_ = "_id"
    USER_ID = "userId"
    PARENT_ID = "parentId"
    TITLE = "title"
    DESCRIPTION = "description"
    MODEL = "model"
    IS_RECURRING = "isRecurring"
    RECURRENCE_PATTERN = "recurrencePattern"
    INSTANCE_EXPIRES_IN = "instanceExpiresIn"
    START_DATE_TIME = "startDateTime"
    END_DATE_TIME = "endDateTime"
    ENABLED = "enabled"
    EXTRA_FIELDS = "extraFields"
    SNOOZING = "snoozing"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"
    COMPLETE_DATE_TIME = "completeDateTime"

    EXTRA_FIELD_NAMES = tuple()

    id: str = default_field(metadata=meta(validate_object_id))
    userId: str = default_field(metadata=meta(validate_object_id))
    title: str = default_field()
    description: str = default_field()
    model: str = required_field()
    isRecurring: bool = field(default=False)
    recurrencePattern: str = default_field()
    instanceExpiresIn: str = field(
        default=DEFAULT_INSTANCE_EXPIRATION_DURATION, metadata=meta(validate_duration)
    )
    startDateTime: str = default_field(metadata=meta(validate_datetime))
    endDateTime: str = default_field(metadata=meta(validate_datetime))
    enabled: bool = field(default=True)
    extraFields: dict = default_field()
    parentId: str = default_field()
    snoozing: list[str] = default_field(
        metadata=meta(lambda x: all([validate_duration(e) for e in x]))
    )
    updateDateTime: str = default_field(metadata=meta(validate_datetime))
    createDateTime: str = default_field(metadata=meta(validate_datetime))
    completeDateTime: str = default_field(metadata=meta(validate_datetime))

    @staticmethod
    def has_child_for(name) -> bool:
        return name in _cls

    @classmethod
    def child(cls, name):
        if name not in _cls:
            raise ClassNotRegisteredException
        return _cls[name]

    @classmethod
    def from_dict(cls, event_dict: dict):
        cls_ = CalendarEvent.child(event_dict["model"])
        event_dict = deepcopy(event_dict)
        extra_fields = event_dict.pop(CalendarEvent.EXTRA_FIELDS, None) or {}
        for field_name in cls_.EXTRA_FIELD_NAMES:
            value = extra_fields.pop(field_name, None)
            event_dict.update({field_name: value} if value else {})
        event_dict.update({cls_.EXTRA_FIELDS: None})
        return from_dict(cls_, event_dict)

    @staticmethod
    def clear(name: str = None):
        global _cls
        if name and name in _cls:
            del _cls[name]
        else:
            _cls = {}

    @staticmethod
    def register(name, sub_class):
        _cls[name] = sub_class

    def to_dict(self, include_none=False, ignored_fields=None):
        instance = deepcopy(self)
        extra_fields_ignored = ignored_fields and self.EXTRA_FIELDS in ignored_fields
        if not extra_fields_ignored:
            instance.pack_extra_fields()
        return to_dict(instance, include_none, ignored_fields)

    def execute(self, run_async=True):
        raise NotImplementedError

    def pack_extra_fields(self):
        raise NotImplementedError

    def as_timezone(self, timezone):
        rrule = self.recurrencePattern
        end_dt = get_dt_from_str(self.endDateTime) if self.endDateTime else None
        self.recurrencePattern = rrule_replace_timezone(rrule, timezone, end_dt)
        return self


@convertibleclass
class CalendarEventLog:
    ID_ = "_id"
    MODEL = "model"
    USER_ID = "userId"
    PARENT_ID = "parentId"
    START_DATE_TIME = "startDateTime"
    END_DATE_TIME = "endDateTime"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"
    SEARCH_KEYS = (MODEL, USER_ID, PARENT_ID)

    id: str = default_field(metadata=meta(validate_id))
    model: str = required_field()
    parentId: str = required_field(metadata=meta(validate_id))
    userId: str = default_field(metadata=meta(validate_id))
    startDateTime: datetime = required_field(metadata=default_datetime_meta())
    endDateTime: datetime = required_field(metadata=default_datetime_meta())
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())

    def as_timezone(self, timezone):
        """Converts local startDateTime/endDateTime in model to UTC time"""
        self.startDateTime = _as_timezone(self.startDateTime, timezone)
        self.endDateTime = _as_timezone(self.endDateTime, timezone)


def _as_timezone(date, tz):
    if isinstance(tz, str):
        tz = pytz.timezone(tz)
    return tz.localize(date).astimezone(pytz.UTC).replace(tzinfo=None)
