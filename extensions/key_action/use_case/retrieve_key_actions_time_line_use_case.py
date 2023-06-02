import pytz

from extensions.key_action.models.key_action_log import KeyAction
from extensions.key_action.use_case.key_action_requests import (
    RetrieveKeyActionsTimeframeRequestObject,
)
from extensions.key_action.use_case.key_action_responses import (
    RetrieveKeyActionsTimeframeResponseObject,
)
from extensions.module_result.models.scheduled_event import ScheduledEvent
from extensions.reminder.models.reminder import UserModuleReminder
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.constants import VALUE_NOT_IN
from sdk.common.usecase.use_case import UseCase


class RetrieveKeyActionsTimelineUseCase(UseCase):
    def __init__(self):
        super().__init__()
        self.service = CalendarService()

    def process_request(self, request_object: RetrieveKeyActionsTimeframeRequestObject):
        exclude_events = [UserModuleReminder.__name__]
        if not self.request_object.user.deployment.features.personalizedConfig:
            exclude_events.append(ScheduledEvent.__name__)

        filter_options = {
            KeyAction.MODEL: {VALUE_NOT_IN: exclude_events},
            KeyAction.USER_ID: request_object.userId,
        }
        key_actions = self.service.retrieve_calendar_events_between_two_dates(
            start=request_object.start,
            end=request_object.end,
            timezone=pytz.timezone(request_object.timezone),
            allow_past_events=request_object.allowPastEvents,
            **filter_options,
        )
        return RetrieveKeyActionsTimeframeResponseObject(
            events=key_actions, localization=request_object.user.localization
        )
