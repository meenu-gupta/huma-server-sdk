import logging
from dataclasses import field, dataclass
from datetime import datetime, timedelta
from typing import Union

import isodate
import pytz
from dateutil import rrule

from sdk.calendar.models.calendar_event import CalendarEvent as Event, CalendarEventLog
from sdk.calendar.utils import get_dt_from_str
from sdk.common.utils.convertible import default_field
from sdk.common.monitoring.monitoring import report_exception
from sdk.common.utils.date_utils import rrule_replace_timezone, to_timezone
from sdk.common.utils.validators import must_be_present, utc_str_field_to_val

logger = logging.getLogger(__name__)


@dataclass
class EventGenerator:
    start: datetime = default_field()
    end: datetime = default_field()
    now: datetime = default_field()
    timezone: pytz.timezone = default_field()
    logs: list[CalendarEventLog] = default_field()
    allow_past_events: bool = field(default=True)
    expiring: bool = field(default=False)
    retrieve_all: bool = field(default=False)

    def __post_init__(self):
        self.timezone = to_timezone(self.timezone)

        if self.retrieve_all:
            return

        if not self.now:
            must_be_present(start=self.start, end=self.end)

        if self.start:
            must_be_present(end=self.end)

    def _as_timezone(self, event: dict):
        if not self.timezone or self.timezone == pytz.UTC:
            return event

        end_dt = event.get(Event.END_DATE_TIME)
        end_dt = get_dt_from_str(end_dt) if end_dt else None
        r_rule = event.get(Event.RECURRENCE_PATTERN)
        r_rule = rrule_replace_timezone(r_rule, self.timezone, end_dt)
        event[Event.RECURRENCE_PATTERN] = r_rule
        return event

    def generate(
        self, events: list, include_snoozing=False, to_model=False, mute_errors=False
    ) -> list:
        generated_events = []
        for event in events:
            try:
                simple_events = self.unpack_event(event, include_snoozing)
                generated_events.extend(simple_events)
            except Exception as error:
                if not mute_errors:
                    raise error
                self._report_error(event, error)

        if to_model:
            result = []
            for event in generated_events:
                try:
                    result.append(Event.from_dict(event))
                except Exception as error:
                    if not mute_errors:
                        raise error
                    self._report_error(event, error)
            return result
        return generated_events

    @staticmethod
    def _report_error(event, error):
        logger.error(f"An error occurred in EventGenerator with error: [{error}]")
        context_name = "Event"
        context_content = {"event": event}

        report_exception(
            error,
            context_name=context_name,
            context_content=context_content,
        )

    def unpack_event_and_disable_completed(
        self, event: Union[dict, Event], include_snoozing=False, only_enabled=False
    ) -> list:
        events = self.unpack_event(event, include_snoozing)
        self.disable_completed_events(events)

        if only_enabled:
            return [ev for ev in events if ev.get(Event.ENABLED)]

        return events

    def unpack_event(self, event: Union[dict, Event], include_snoozing=False) -> list:
        if not isinstance(event, dict):
            event = event.to_dict(include_none=False)

        return self._unpack_event(event, include_snoozing)

    def _unpack_event(self, event: dict, include_snoozing=False) -> list[dict]:
        self._as_timezone(event)
        if event.get(Event.IS_RECURRING):
            return self.extract_events_from_recurring_event(event, include_snoozing)
        else:
            start = get_dt_from_str(event.get(Event.START_DATE_TIME))
            end = get_dt_from_str(event.get(Event.END_DATE_TIME))
            event[Event.PARENT_ID] = event[Event.ID]
            return [event] if self.is_valid_date(start, end) else []

    def extract_events_from_recurring_event(self, event: dict, include_snoozing=False):
        default_expiration = Event.DEFAULT_INSTANCE_EXPIRATION_DURATION
        instance_expires_in = event.get(Event.INSTANCE_EXPIRES_IN) or default_expiration
        pattern = event.get(Event.RECURRENCE_PATTERN)
        rule = self.safe_rrule(pattern, instance_expires_in)
        base_event_duration = isodate.parse_duration(instance_expires_in)
        event_end = event.get(Event.END_DATE_TIME)
        if event_end:
            event_end = get_dt_from_str(event_end)
        event_duration = base_event_duration - timedelta(minutes=1)

        generated_events = []
        for start in rule:
            end = start + event_duration
            if event_end and event_end < end:
                end = event_end

            simple_event = None
            if self.is_valid_date(start, end):
                simple_event = self.complex_event_to_simple_event(event, start, end)
                generated_events.append(simple_event)
            elif end is event_end:
                break
            if include_snoozing and event.get(Event.SNOOZING):
                snoozing_events = self.extract_valid_snoozing_events(event, start, end)
                generated_events.extend(snoozing_events)
                if not simple_event:
                    continue
                # remove snoozing from initial event
                simple_event.pop(Event.SNOOZING, None)

        return generated_events

    def extract_valid_snoozing_events(
        self, event: dict, start: datetime, end: datetime
    ):
        events = []
        for snoozing in event.get(Event.SNOOZING, []):
            delta = isodate.parse_duration(snoozing)
            snoozing_start = start + delta
            if not self.is_valid_date(snoozing_start, end):
                continue
            simple_event = self.complex_event_to_simple_event(
                event, snoozing_start, end
            )
            simple_event.pop(Event.SNOOZING, None)
            events.append(simple_event)
        return events

    def safe_rrule(self, r_rule: str, instance_exp_in: str):
        """Prevents infinite loops by adding until date if not present."""
        if not r_rule:
            return None
        rule = rrule.rrulestr(r_rule)
        if not rule._until:
            until = self.end
            if not until:
                default_duration = isodate.parse_duration(instance_exp_in)
                now = self.now or datetime.utcnow()
                until = now + default_duration
            rule = rule.replace(until=until)
        return rule

    @staticmethod
    def complex_event_to_simple_event(
        event: dict, start: datetime, end: datetime = None
    ):
        snoozing_str_start = utc_str_field_to_val(start)
        snoozing_str_end = utc_str_field_to_val(end) if end else snoozing_str_start
        event = {
            **event,
            Event.START_DATE_TIME: snoozing_str_start,
            Event.END_DATE_TIME: snoozing_str_end,
            Event.PARENT_ID: event.get(Event.ID),
        }
        event.pop(Event.IS_RECURRING, None)
        event.pop(Event.RECURRENCE_PATTERN, None)
        return event

    def is_valid_date(self, start: datetime, end: datetime):
        if self.retrieve_all:
            return True

        if self.start and self.end:
            if self.expiring:
                return self.start <= end <= self.end

            if self.allow_past_events:
                return start < self.end and end > self.start
            else:
                return self.start <= start < self.end and end > self.start
        else:
            return start <= self.now <= end

    def disable_completed_events(
        self, events: list[dict], logs: list[CalendarEventLog] = None
    ):
        for event in events:
            self.disable_completed_event(event, logs)

    def disable_completed_event(self, event: dict, logs: list[CalendarEventLog] = None):
        logs = logs or self.logs or []
        event_start = event.get(Event.START_DATE_TIME)
        log = self.find_log_match(event.get(Event.ID), event_start, logs)
        if not log:
            return
        new_data = {
            Event.ID: log.id,
            Event.ENABLED: False,
            Event.COMPLETE_DATE_TIME: utc_str_field_to_val(log.createDateTime),
        }
        event.update(new_data)

    @staticmethod
    def find_log_match(event_id, event_start, logs: list[CalendarEventLog]):
        def log_match(item: CalendarEventLog):
            match = item.parentId == event_id
            return match and item.startDateTime == get_dt_from_str(event_start)

        return next((log for log in logs if log_match(log)), None)
