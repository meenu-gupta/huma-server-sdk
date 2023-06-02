import functools
from datetime import timedelta, datetime

from sdk.common.utils import inject
from sdk.common.utils.validators import utc_str_val_to_field
from sdk.phoenix.config.server_config import PhoenixServerConfig


def get_calendar_prefetch_timedelta():
    config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
    days = config.server.calendar.prefetchDays or 0
    if days > 0:
        return timedelta(days=days - 1, hours=23, minutes=59)
    return timedelta(days=days)


def no_seconds(dt: datetime):
    return dt.replace(second=0, microsecond=0)


def now_no_seconds():
    return no_seconds(datetime.utcnow())


@functools.lru_cache(maxsize=60)
def get_dt_from_str(value: str):
    return utc_str_val_to_field(value)


def get_start_end_for_today():
    start = now_no_seconds()
    if start.hour >= 3:
        end = start + timedelta(days=1)
    else:
        end = start
    end = end.replace(hour=3, minute=1)
    return start, end
