import typing
from datetime import timedelta, datetime

import isodate

from extensions.appointment.models.appointment import Appointment
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.key_action.models.key_action_log import KeyAction
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.calendar.utils import get_dt_from_str
from sdk.common.utils.validators import remove_none_values, utc_str_field_to_val


def key_action_config_filter_by_id(
    key_actions: list[KeyActionConfig], _id: str
) -> typing.Generator[KeyActionConfig, None, None]:
    if not key_actions:
        yield from ()
    for action in key_actions:
        if action.id == _id:
            yield action


def key_action_config_filter_by_trigger(
    key_actions: list[KeyActionConfig], trigger: KeyActionConfig.Trigger
):
    yield from filter(lambda a: a.trigger == trigger, key_actions)


def key_action_to_dict(key_action: CalendarEvent):
    if isinstance(key_action, Appointment):
        correlate_appointments_start_time(key_action)
    _dict = key_action.to_dict(ignored_fields=[CalendarEvent.EXTRA_FIELDS])
    _dict.pop(KeyAction.SNOOZING, None)
    return remove_none_values(_dict)


def correlate_appointments_start_time(appointment: Appointment):
    start = get_dt_from_str(appointment.startDateTime)
    end = get_dt_from_str(appointment.endDateTime)
    delta = isodate.parse_duration(appointment.instanceExpiresIn)
    correlated_datetime = get_correlated_start_time(start, end, delta)
    appointment.appointmentDateTime = utc_str_field_to_val(correlated_datetime)


def get_correlated_start_time(start: datetime, end: datetime, expiration_delta):
    if start != end or (end - start) > timedelta(hours=2):
        return start + expiration_delta
    else:
        return end
