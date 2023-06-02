from extensions.key_action.utils import key_action_to_dict
from sdk import convertibleclass, meta
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.usecase import response_object
from sdk.common.utils.convertible import required_field
from sdk.common.utils.json_utils import replace_values


def events_to_dict(events: list[CalendarEvent]):
    return [key_action_to_dict(key_action) for key_action in events]


class RetrieveKeyActionsTimeframeResponseObject(response_object.Response):
    localization = None

    @convertibleclass
    class Response:
        EVENTS = "events"

        events: list[CalendarEvent] = required_field(
            metadata=meta(field_to_value=events_to_dict)
        )

    def __init__(self, events: list[CalendarEvent], localization: dict):
        value = self.Response.from_dict({self.Response.EVENTS: events})
        self.localization = localization
        super().__init__(value)

    def to_list(self):
        events = self.value.to_dict()["events"]
        return [replace_values(event, self.localization) for event in events]
