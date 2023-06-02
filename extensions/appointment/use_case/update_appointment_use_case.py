from datetime import datetime, timedelta

import i18n

from extensions.appointment.models.appointment import Appointment
from extensions.appointment.models.appointment_event import AppointmentEvent as Event
from extensions.appointment.repository.appointment_repository import (
    AppointmentRepository,
)
from extensions.appointment.router.appointment_requests import (
    UpdateAppointmentRequestObject,
    RetrieveAppointmentRequestObject,
)
from extensions.appointment.use_case.base_appointment_use_case import (
    BaseAppointmentUseCase,
)
from extensions.appointment.use_case.retrieve_appointment_use_case import (
    RetrieveAppointmentUseCase,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from sdk.calendar.service.calendar_service import CalendarService
from sdk.calendar.utils import no_seconds, now_no_seconds
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.usecase.response_object import Response
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import utc_str_field_to_val as to_str


class UpdateAppointmentUseCase(BaseAppointmentUseCase):
    BEFORE_HOURS = 3
    old_appointment: Appointment = None
    language: str = None

    @autoparams()
    def __init__(self, auth_repo: AuthorizationRepository, repo: AppointmentRepository):
        self._auth_repo = auth_repo
        self._repo = repo

    def process_request(self, request_object: UpdateAppointmentRequestObject):
        self.validate_and_set_defaults()
        self.request_object.isUser = None
        appointment = self._repo.update_appointment(request_object.id, request_object)
        self.trigger_events_based_on_updated_fields(appointment)
        self._repo.update_appointment(request_object.id, appointment)
        return Response(appointment.id)

    def validate_and_set_defaults(self):
        self.fetch_old_appointment()
        self.validate()
        self._set_defaults()

    def trigger_events_based_on_updated_fields(self, appointment: Appointment):
        if appointment.is_rescheduled(self.old_appointment):
            self._delete_connected_calendar_event(appointment)
            self._create_pending_key_action(appointment)

        elif appointment.is_status_changed(self.old_appointment):
            self._delete_connected_calendar_event(appointment)
            if appointment.status is Appointment.Status.SCHEDULED:
                self._create_reminder_key_action(appointment)
            else:
                self._repo.unset_key_action(appointment.id)

    def fetch_old_appointment(self):
        req = RetrieveAppointmentRequestObject.from_dict(
            {RetrieveAppointmentRequestObject.APPOINTMENT_ID: self.request_object.id}
        )
        self.old_appointment = RetrieveAppointmentUseCase().execute(req).value

    def validate(self):
        new = self.request_object
        old = self.old_appointment
        time_left_until_call = old.startDateTime - datetime.utcnow()

        if self.request_object.isUser:
            if old.status is not Appointment.Status.PENDING_CONFIRMATION:
                if time_left_until_call < timedelta(hours=self.BEFORE_HOURS):
                    raise InvalidRequestException(
                        f"Appointment can not be updated in last {self.BEFORE_HOURS} hours"
                    )

        if new.userId and new.userId != old.userId:
            raise InvalidRequestException("Can't change assigned user")

        if not new.status or new.status is old.status:
            return

        allowed_statuses = old.status.retrieve_next_statuses()
        if new.status not in allowed_statuses:
            msg = f"Update appointment with next status [%s] is not allowed for the current status [%s]"
            raise InvalidRequestException(msg % (new.status.name, old.status.name))

    def _set_defaults(self):
        get_profile = self._auth_repo.retrieve_simple_user_profile
        user = get_profile(user_id=self.request_object.userId)
        if self.request_object.is_rescheduled(self.old_appointment):
            self.request_object.status = Appointment.Status.PENDING_CONFIRMATION

        user = AuthorizedUser(user)
        self.language = user.get_language()

    @staticmethod
    def _create_pending_key_action(appointment: Appointment) -> str:
        data = {
            Event.MODEL: Appointment.__name__,
            Event.TITLE: appointment.title,
            Event.DESCRIPTION: appointment.description,
            Event.START_DATE_TIME: to_str(now_no_seconds()),
            Event.END_DATE_TIME: to_str(appointment.endDateTime),
            Event.USER_ID: appointment.userId,
            Event.APPOINTMENT_DATE_TIME: to_str(appointment.startDateTime),
            Event.APPOINTMENT_ID: appointment.id,
            Event.APPOINTMENT_STATUS: appointment.status.value,
        }
        event: Event = Event.from_dict(data)
        event_id = CalendarService().create_calendar_event(event)
        event.execute()
        appointment.keyActionId = event_id
        return event_id

    def _create_reminder_key_action(self, appointment: Appointment) -> str:
        reminder_time = no_seconds(appointment.startDateTime - timedelta(hours=1))
        data = {
            Event.MODEL: Appointment.__name__,
            Event.TITLE: i18n.t("Appointment.Reminder.title", locale=self.language),
            Event.DESCRIPTION: i18n.t(
                "Appointment.Reminder.body", locale=self.language
            ),
            Event.START_DATE_TIME: to_str(reminder_time),
            Event.END_DATE_TIME: to_str(appointment.endDateTime),
            Event.USER_ID: appointment.userId,
            Event.APPOINTMENT_DATE_TIME: to_str(appointment.startDateTime),
            Event.APPOINTMENT_ID: appointment.id,
            Event.APPOINTMENT_STATUS: appointment.status.value,
        }
        event: Event = Event.from_dict(data)
        event_id = CalendarService().create_calendar_event(event)
        appointment.keyActionId = event_id
        return event_id

    @staticmethod
    def _delete_connected_calendar_event(appointment: Appointment):
        if appointment.keyActionId:
            CalendarService().delete_calendar_event(appointment.keyActionId)
            appointment.keyActionId = None
