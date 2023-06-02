import math
from datetime import datetime, timedelta

import pytz
from dateutil import rrule

from extensions.module_result.models.module_config import CustomModuleConfig, Weekday
from extensions.module_result.models.scheduled_event import ScheduledEvent
from sdk.common.utils.date_utils import (
    get_interval_from_duration_iso,
    get_time_from_duration_iso as convert,
)

weekday_map = {
    Weekday.MON: rrule.MO,
    Weekday.TUE: rrule.TU,
    Weekday.WED: rrule.WE,
    Weekday.THU: rrule.TH,
    Weekday.FRI: rrule.FR,
    Weekday.SAT: rrule.SA,
    Weekday.SUN: rrule.SU,
}


def to_scheduled_events(
    config: CustomModuleConfig, timezone: str
) -> list[ScheduledEvent]:
    """
    Generate a list of Scheduled events based on the config provided.
    All events are recursive, rrule depends on config.schedule object.
    Every instance expires a minute before next event starts but not less than 15 minutes after it started.
    """
    if not (schedule := config.schedule):
        return []

    interval = get_interval_from_duration_iso(schedule.isoDuration)
    tz = pytz.timezone(timezone)
    start_dt = datetime.now(tz).replace(tzinfo=None)

    start_times = _to_sorted_dates_list(schedule.timesOfReadings or [])
    events = []
    for next_index, start in enumerate(start_times, 1):
        if next_index < len(start_times):
            next_event_start = start_times[next_index]
        else:
            next_event_start = start_times[0] + timedelta(days=1)

        rule = rrule.rrule(
            freq=rrule.WEEKLY,
            interval=interval,
            dtstart=start_dt,
            byweekday=tuple(weekday_map[day] for day in schedule.specificWeekDays),
            byhour=start.hour,
            byminute=start.minute,
            bysecond=0,
        )
        event = ScheduledEvent(
            isRecurring=True,
            moduleId=config.moduleId,
            moduleConfigId=config.id,
            recurrencePattern=str(rule),
            userId=config.userId,
            startDateTime=start_dt,
            model=ScheduledEvent.__name__,
            instanceExpiresIn=_get_expire_duration(start, next_event_start),
        )
        events.append(event)

    return events


def _to_sorted_dates_list(durations: list[str]):
    now = datetime.utcnow()
    start_times = [datetime.combine(now, convert(t)) for t in durations]
    start_times.sort()
    return start_times


def _get_expire_duration(start_dt: datetime, next_start_dt: datetime):
    expires_in_seconds = (next_start_dt - start_dt).total_seconds()
    expires_in_minutes = max(expires_in_seconds / 60, 15)
    return f"PT{math.floor(expires_in_minutes)}M"
