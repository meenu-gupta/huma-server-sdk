import typing
from datetime import datetime, timedelta, date

import isodate
import pytz
from dateutil import rrule
from isodate import duration_isoformat

from extensions.authorization.models.user import User
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.key_action.models.key_action_log import KeyAction
from sdk.calendar.utils import no_seconds, now_no_seconds
from sdk.common.utils.date_utils import (
    get_time_from_duration_iso,
    get_interval_from_duration_iso,
)
from sdk.common.utils.validators import utc_str_field_to_val, remove_none_values


class KeyActionGenerator:
    def __init__(
        self,
        user: typing.Optional[User],
        trigger_time: typing.Union[date, datetime],
        deployment_id: str,
    ):
        self.user = user
        self.deployment_id = deployment_id
        if isinstance(trigger_time, datetime):
            self.trigger_time = no_seconds(trigger_time)
        elif isinstance(trigger_time, date):
            self.trigger_time = datetime.combine(trigger_time, datetime.min.time())
        else:
            raise Exception(f"Expected type date or datetime, got {type(trigger_time)}")

    def build_key_action_from_config(self, config: KeyActionConfig) -> KeyAction:
        event_time = get_time_from_duration_iso(config.durationIso)
        delta_from_trigger = isodate.parse_duration(config.deltaFromTriggerTime)
        start = self.trigger_time + delta_from_trigger
        dtstart = start
        first_event = KeyActionGenerator.get_utc_time(
            hour=event_time.hour,
            minute=event_time.minute,
            timezone=pytz.timezone(self.user.timezone)
            if self.user
            else pytz.timezone("UTC"),
        ).replace(tzinfo=None)
        dtstart = dtstart.replace(hour=first_event.hour, minute=first_event.minute)
        until = (
            start
            + isodate.parse_duration(config.durationFromTrigger)
            - timedelta(minutes=1)
        )
        r_rule = rrule.rrule(
            freq=KeyActionGenerator.set_freq(config.durationIso),
            dtstart=dtstart,
            interval=get_interval_from_duration_iso(config.durationIso),
            byhour=event_time.hour,
            byminute=event_time.minute,
            until=until,
            cache=True,
        )
        event_dict = {
            KeyAction.KEY_ACTION_CONFIG_ID: config.id,
            KeyAction.TITLE: config.title,
            KeyAction.DESCRIPTION: config.description,
            KeyAction.IS_RECURRING: True,
            KeyAction.DEPLOYMENT_ID: self.deployment_id,
            KeyAction.START_DATE_TIME: utc_str_field_to_val(start),
            KeyAction.END_DATE_TIME: utc_str_field_to_val(until),
            KeyAction.RECURRENCE_PATTERN: str(r_rule),
            KeyAction.INSTANCE_EXPIRES_IN: config.instanceExpiresIn,
            KeyAction.MODEL: KeyAction.__name__,
            KeyAction.SNOOZING: KeyActionGenerator.build_snoozing(
                config.notifyEvery, config.numberOfNotifications
            )
            or None,
        }
        if self.user:
            event_dict[KeyAction.USER_ID] = self.user.id

        if config.type == KeyActionConfig.Type.MODULE:
            event_dict.update(
                {
                    KeyAction.MODULE_ID: config.moduleId,
                    KeyAction.MODULE_CONFIG_ID: config.moduleConfigId,
                }
            )
        elif config.type == KeyActionConfig.Type.LEARN:
            event_dict.update({KeyAction.LEARN_ARTICLE_ID: config.learnArticleId})

        return KeyAction.from_dict(remove_none_values(event_dict))

    @staticmethod
    def build_snoozing(duration, count) -> list[str]:
        """Calculates iso duration values for given notification count."""
        if not duration:
            return []
        delta: timedelta = isodate.parse_duration(duration)
        return [duration_isoformat(delta * i) for i in range(1, count + 1)]

    @staticmethod
    def set_freq(duration: str) -> int:
        duration = duration.split("T")[0]

        duration_mapping = {
            "Y": rrule.YEARLY,
            "M": rrule.MONTHLY,
            "W": rrule.WEEKLY,
            "D": rrule.DAILY,
        }
        for key in duration_mapping:
            if key in duration:
                return duration_mapping[key]

        raise Exception("Supported durations are Y, M, W, D")

    @staticmethod
    def get_utc_time(hour, minute, timezone):
        _temp = now_no_seconds().replace(hour=hour, minute=minute)
        return timezone.localize(_temp).astimezone(pytz.UTC)
