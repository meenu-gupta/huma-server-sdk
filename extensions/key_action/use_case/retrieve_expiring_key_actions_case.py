import pytz

from extensions.key_action.models.key_action_log import KeyAction
from extensions.key_action.use_case.key_action_requests import (
    RetrieveExpiringKeyActionsRequestObject,
)
from extensions.key_action.use_case.key_action_responses import (
    RetrieveKeyActionsTimeframeResponseObject,
)
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.usecase.use_case import UseCase


class RetrieveExpiringKeyActionsUseCase(UseCase):
    def __init__(self):
        self.service = CalendarService()

    def process_request(self, request_object: RetrieveExpiringKeyActionsRequestObject):
        filter_options = {
            KeyAction.MODEL: KeyAction.__name__,
            KeyAction.USER_ID: request_object.userId,
        }
        key_actions = self.service.retrieve_calendar_events_between_two_dates(
            start=request_object.start,
            end=request_object.end,
            timezone=pytz.timezone(request_object.timezone),
            expiring=True,
            **filter_options,
        )

        if request_object.onlyEnabled:
            key_actions = [ka for ka in key_actions if ka.enabled]

        return RetrieveKeyActionsTimeframeResponseObject(
            events=key_actions, localization=request_object.user.localization
        )
