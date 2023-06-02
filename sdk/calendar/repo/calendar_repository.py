from abc import ABC, abstractmethod

from pymongo.client_session import ClientSession

from sdk.calendar.models.calendar_event import CalendarEvent, CalendarEventLog


class CalendarRepository(ABC):
    @abstractmethod
    def create_calendar_event(self, event: CalendarEvent):
        raise NotImplementedError

    @abstractmethod
    def create_calendar_event_log(self, event: CalendarEventLog):
        raise NotImplementedError

    @abstractmethod
    def create_next_day_events(self, events: list[CalendarEvent]):
        raise NotImplementedError

    @abstractmethod
    def batch_create_calendar_events(self, events: list[CalendarEvent]):
        raise NotImplementedError

    @abstractmethod
    def retrieve_calendar_event(self, event_id: str):
        raise NotImplementedError

    @abstractmethod
    def retrieve_calendar_events(self, mute_errors=False, **options):
        raise NotImplementedError

    @abstractmethod
    def retrieve_calendar_event_logs(self, **options):
        raise NotImplementedError

    @abstractmethod
    def update_calendar_event(self, event_id: str, event: CalendarEvent):
        raise NotImplementedError

    @abstractmethod
    def delete_calendar_event(self, event_id: str):
        raise NotImplementedError

    @abstractmethod
    def batch_delete_calendar_events(self, filter_options: dict):
        raise NotImplementedError

    @abstractmethod
    def batch_delete_calendar_events_by_ids(self, ids: list[str]):
        raise NotImplementedError

    @abstractmethod
    def batch_delete_next_day_events_by_parent_ids(self, parent_ids: list[str]) -> int:
        raise NotImplementedError

    @abstractmethod
    def retrieve_next_day_events(self, filter_options) -> list[CalendarEvent]:
        raise NotImplementedError

    @abstractmethod
    def batch_delete_next_day_events(self, event_ids: list[str]):
        raise NotImplementedError

    @abstractmethod
    def batch_delete_next_day_events_for_user(self, user_id: str):
        raise NotImplementedError

    @abstractmethod
    def batch_delete_next_day_event_raw(self, filter_options):
        raise NotImplementedError

    @abstractmethod
    def clear_cached_events(self):
        raise NotImplementedError

    @abstractmethod
    def delete_user_events(self, user_id: str, session: ClientSession = None):
        raise NotImplementedError

    def update_events_status(self, filter_options: dict, status: bool) -> int:
        raise NotImplementedError
