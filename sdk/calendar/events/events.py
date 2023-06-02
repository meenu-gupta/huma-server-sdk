from sdk.common.adapter.event_bus_adapter import BaseEvent


class RequestUsersTimezonesEvent(BaseEvent):
    """ Event that is emitted to retrieve users by ids for executing events. """

    def __init__(self, ids: list = None):
        self.ids = ids or []


class PostBatchCreateCalendarEvent(BaseEvent):
    pass


class PostBatchDeleteCalendarEventsEvent(BaseEvent):
    pass


class CalendarViewUserDataEvent(BaseEvent):
    pass


class CreateCalendarLogEvent(BaseEvent):
    def __init__(self, user_id: str):
        self.user_id = user_id
