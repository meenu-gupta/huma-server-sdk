import logging
from datetime import datetime
from typing import Union
import pytz
from ics import Calendar, Event
from pymongo.client_session import ClientSession

from sdk.calendar.events import CreateCalendarLogEvent
from sdk.calendar.models.calendar_event import CalendarEvent, CalendarEventLog
from sdk.calendar.models.event_generator import EventGenerator
from sdk.calendar.repo.calendar_repository import CalendarRepository
from sdk.calendar.utils import get_start_end_for_today
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.constants import LESS_OR_EQUAL_TO
from sdk.common.monitoring.monitoring import report_exception
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.date_utils import get_dt_now_as_str
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import (
    utc_str_val_to_field,
    remove_none_values,
    utc_str_field_to_val,
)

logger = logging.getLogger(__name__)


class CalendarService:
    @autoparams()
    def __init__(self, repo: CalendarRepository, event_bus: EventBusAdapter):
        self._repo = repo
        self._event_bus = event_bus

    def create_calendar_event(self, event: CalendarEvent, timezone=None) -> str:
        event.createDateTime = event.updateDateTime = get_dt_now_as_str()
        event_id = self._repo.create_calendar_event(event)
        event.id = event_id
        self.create_next_day_event(event, timezone)
        return event.id

    def create_calendar_event_log(self, event: CalendarEventLog) -> str:
        event.createDateTime = event.updateDateTime = datetime.utcnow()
        result = self._repo.create_calendar_event_log(event)
        self._repo.batch_delete_next_day_events_by_parent_ids([event.parentId])
        self._event_bus.emit(CreateCalendarLogEvent(user_id=event.userId))
        return result

    def create_next_day_event(self, event: CalendarEvent, timezone: str, clear=False):
        logs = self.retrieve_calendar_event_logs(parentId=event.id, timezone=timezone)
        start, end = get_start_end_for_today()
        generator = EventGenerator(
            start, end, timezone=timezone, logs=logs, allow_past_events=False
        )

        events = generator.unpack_event_and_disable_completed(event, only_enabled=True)
        if clear:
            self._repo.batch_delete_next_day_events_by_parent_ids([event.id])

        if not events:
            return

        events = generator.unpack_event_and_disable_completed(
            event, include_snoozing=True, only_enabled=True
        )

        new_events = []
        for event in events:
            event.pop(CalendarEvent.ID, None)
            event_dict = remove_none_values(event)
            new_events.append(CalendarEvent.from_dict(event_dict))

        self._repo.create_next_day_events(new_events)

    def batch_create_calendar_events(self, events):
        return self._repo.batch_create_calendar_events(events)

    def retrieve_calendar_event(self, event_id: str) -> CalendarEvent:
        return self._repo.retrieve_calendar_event(event_id)

    def retrieve_raw_events(
        self, mute_errors=False, **options
    ) -> list[Union[dict, CalendarEvent]]:
        return self._repo.retrieve_calendar_events(mute_errors=mute_errors, **options)

    def _retrieve_calendar_events(
        self, generator: EventGenerator, timezone=None, **options
    ):
        to_model = options.pop("to_model", True)
        raw_events = self.retrieve_raw_events(**options, to_model=False)
        events = generator.generate(raw_events)

        logs = self.retrieve_calendar_event_logs(**options, timezone=timezone)
        generator.disable_completed_events(events, logs)

        if to_model:
            events = [CalendarEvent.from_dict(event) for event in events]
        return events

    def retrieve_calendar_events(
        self,
        compare_dt: datetime,
        timezone=None,
        **options,
    ) -> list[Union[dict, CalendarEvent]]:
        """
        options: ORM filter options to filter events. Example: {"model": "KeyAction"}
        """
        allow_past_events = options.pop("allow_past_events", True)
        generator = EventGenerator(
            now=compare_dt, timezone=timezone, allow_past_events=allow_past_events
        )
        return self._retrieve_calendar_events(generator, timezone=timezone, **options)

    def retrieve_all_calendar_events(self, timezone=None, **options):
        generator = EventGenerator(retrieve_all=True, timezone=timezone)
        return self._retrieve_calendar_events(generator, timezone=timezone, **options)

    def retrieve_calendar_events_between_two_dates(
        self, start: datetime, end: datetime, timezone=None, **options
    ) -> list[Union[dict, CalendarEvent]]:
        """
        options: ORM filter options to filter events. Example: {"model": "KeyAction"}
        """
        allow_past_events = options.pop("allow_past_events", True)
        expiring = options.pop("expiring", False)
        generator = EventGenerator(
            start=start,
            end=end,
            timezone=timezone,
            allow_past_events=allow_past_events,
            expiring=expiring,
        )
        return self._retrieve_calendar_events(generator, timezone=timezone, **options)

    def retrieve_calendar_event_logs(self, **options) -> list[CalendarEventLog]:
        timezone = options.pop("timezone", None)

        def is_valid(key):
            return key.startswith(CalendarEventLog.SEARCH_KEYS)

        log_filter_options = {k: v for k, v in options.items() if is_valid(k)}
        logs = self._repo.retrieve_calendar_event_logs(**log_filter_options)
        if not timezone:
            return logs

        # TODO remove reference to extensions appointment
        for log in logs:
            if log.model == "Appointment":
                continue
            log.as_timezone(timezone)

        return logs

    def update_calendar_event(self, event_id: str, event: CalendarEvent, timezone: str):
        event.updateDateTime = utc_str_field_to_val(datetime.utcnow())
        updated_event = self._repo.update_calendar_event(event_id, event)
        self.create_next_day_event(updated_event, timezone=timezone, clear=True)
        return updated_event.id

    def delete_calendar_event(self, event_id: str):
        result = self._repo.delete_calendar_event(event_id)
        self._repo.batch_delete_next_day_events_by_parent_ids([event_id])
        return result

    def batch_delete_calendar_events(self, filter_options: dict):
        deleted_ids = self._repo.batch_delete_calendar_events(filter_options)
        if deleted_ids:
            self._repo.batch_delete_next_day_events_by_parent_ids(deleted_ids)
        return deleted_ids

    def batch_delete_calendar_events_by_ids(self, ids: list[str]) -> list[str]:
        self._repo.batch_delete_calendar_events_by_ids(ids=ids)
        self._repo.batch_delete_next_day_events_by_parent_ids(parent_ids=ids)

        return ids

    def export_calendar(self, start, end, timezone, debug=False, **options):
        events = self.retrieve_calendar_events_between_two_dates(
            start, end, timezone, **options
        )
        calendar = Calendar()
        for event in events:
            logger.debug(f"export calendar event : {event}")
            try:
                new_event = Event(
                    name=event.title or str(event),
                    description=self._set_event_description(event, debug),
                    begin=utc_str_val_to_field(event.startDateTime),
                    end=utc_str_val_to_field(event.endDateTime),
                    created=utc_str_val_to_field(event.createDateTime),
                    last_modified=utc_str_val_to_field(event.updateDateTime),
                )
            except Exception as error:
                logger.error(f"Exporting failed for event {event}.\nError: {error}")
                report_exception(
                    error,
                    context_name="ExportCalendar",
                    context_content={"start": start, "end": end, "timezone": timezone},
                )
            else:
                calendar.events.add(new_event)
        return calendar

    @staticmethod
    def _set_event_description(event, debug=False):
        if debug:
            return (
                f"Event Description: {event.description} \n"
                f"Instance Expires In: {event.instanceExpiresIn} \n"
                f"Completed: {not event.enabled} \n"
            )
        else:
            return event.description

    def retrieve_next_day_events(self, filter_options) -> list[CalendarEvent]:
        return self._repo.retrieve_next_day_events(filter_options)

    def calculate_and_save_next_day_events(self, user_timezones: dict):
        start, end = get_start_end_for_today()
        events = self.retrieve_raw_events(
            mute_errors=True, **{CalendarEvent.START_DATE_TIME: {LESS_OR_EQUAL_TO: end}}
        )
        valid_events = []
        events_without_user = []
        for event in events:
            if event.userId not in user_timezones:
                logger.warning(
                    f"No user found for event {event.parentId}. User ID: {event.userId}. Skipping."
                )
                events_without_user.append(event.id)
                continue

            user_tz = user_timezones[event.userId]
            if user_tz and user_tz != pytz.UTC.zone:
                event.as_timezone(pytz.timezone(user_tz))

            valid_events.append(event)

        generator = EventGenerator(start=start, end=end, allow_past_events=False)
        new_events = generator.generate(
            valid_events, include_snoozing=True, to_model=True, mute_errors=True
        )

        for event in new_events:
            event.parentId = event.parentId or event.id
            event.id = None

        if events_without_user:
            self.batch_delete_calendar_events_by_ids(events_without_user)

        self.clear_cached_events()
        if new_events:
            return self.save_next_day_events(new_events)
        return None

    def calculate_and_save_next_day_events_for_user(self, user_id, timezone):
        start, end = get_start_end_for_today()
        events = self.retrieve_raw_events(
            **{
                CalendarEvent.START_DATE_TIME: {LESS_OR_EQUAL_TO: end},
                CalendarEvent.USER_ID: user_id,
            }
        )
        generator = EventGenerator(
            start, end, timezone=timezone, allow_past_events=False
        )
        new_events = generator.generate(events, include_snoozing=True, to_model=True)

        for event in new_events:
            event.parentId = event.parentId or event.id
            event.id = None

        self._repo.batch_delete_next_day_events_for_user(user_id)
        if new_events:
            return self.save_next_day_events(new_events)

    def save_next_day_events(self, events: list[CalendarEvent]):
        return self._repo.create_next_day_events(events)

    def batch_delete_next_day_events(self, events_ids: list[str]):
        return self._repo.batch_delete_next_day_events(events_ids)

    def batch_delete_next_day_events_by_parent_ids(self, parent_ids: list[str]):
        return self._repo.batch_delete_next_day_events_by_parent_ids(parent_ids)

    def clear_cached_events(self):
        return self._repo.clear_cached_events()

    def delete_user_events(self, user_id: str, session: ClientSession = None):
        self._repo.delete_user_events(session=session, user_id=user_id)

    def update_events_status(self, filter_options: dict, status: bool) -> int:
        """Changes matching events' status and returns the number of updated events"""
        return self._repo.update_events_status(filter_options, status)
