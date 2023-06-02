import pytz

from extensions.key_action.use_case.key_action_requests import (
    RetrieveKeyActionsTimeframeRequestObject,
)
from extensions.key_action.utils import key_action_to_dict
from extensions.module_result.models.scheduled_event import ScheduledEvent
from extensions.reminder.models.reminder import UserModuleReminder
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.constants import VALUE_NOT_IN
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.json_utils import replace_values


class RetrieveKeyActionsUseCase(UseCase):
    def __init__(self):
        super().__init__()
        self.service = CalendarService()

    def process_request(
        self, request_object: RetrieveKeyActionsTimeframeRequestObject
    ) -> Response:
        exclude_events = [UserModuleReminder.__name__]
        if not self.request_object.user.deployment.features.personalizedConfig:
            exclude_events.append(ScheduledEvent.__name__)

        key_actions = self.service.retrieve_calendar_events(
            compare_dt=request_object.start,
            timezone=pytz.timezone(request_object.timezone),
            userId=request_object.userId,
            model={VALUE_NOT_IN: exclude_events},
        )
        events = [key_action_to_dict(action) for action in key_actions]
        events = [
            replace_values(event, request_object.user.localization) for event in events
        ]
        return Response(events)
