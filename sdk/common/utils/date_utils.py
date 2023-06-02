from datetime import date, datetime, time

import isodate
from dateutil import rrule
import pytz

from sdk.calendar.utils import no_seconds
from sdk.common.constants import SEC_IN_HOUR


def calculate_age(birth_date):
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


def get_dt_now_as_str():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def rrule_replace_timezone(pattern: str, timezone, end_dt: datetime) -> str:
    if not pattern:
        return pattern

    r_rule = rrule.rrulestr(pattern, cache=True)
    (hour,), (minute,) = r_rule._byhour, r_rule._byminute
    old_start_date = no_seconds(r_rule._dtstart).date()
    start_time_local = time(hour=hour, minute=minute)
    dt_start_naive = datetime.combine(old_start_date, start_time_local)
    dt_start = timezone.localize(dt_start_naive).astimezone(pytz.UTC)
    until = timezone.localize(end_dt).astimezone(pytz.UTC) if end_dt else None
    new_rule = r_rule.replace(
        dtstart=dt_start, byhour=dt_start.hour, byminute=dt_start.minute, until=until
    )
    return str(new_rule)


def to_timezone(tz) -> pytz.timezone:
    if isinstance(tz, str):
        return pytz.timezone(tz)

    return tz


def get_time_from_duration_iso(duration_iso: str):
    duration = isodate.parse_duration(duration_iso)
    hours = duration.seconds // SEC_IN_HOUR
    minutes = int((duration.seconds % SEC_IN_HOUR) / 60)
    return time(hour=hours, minute=minutes)


def get_interval_from_duration_iso(duration: str) -> int:
    duration_date_part = duration.split("T")[0]
    res = 0

    if "Y" in duration_date_part:
        res = isodate.parse_duration(duration).years

    elif "M" in duration_date_part:
        res = isodate.parse_duration(duration).months

    elif "W" in duration_date_part:
        res = isodate.parse_duration(duration).days / 7

    elif "D" in duration_date_part:
        res = isodate.parse_duration(duration).days

    if not res:
        raise ValueError("Interval can not be 0")

    return int(res)
