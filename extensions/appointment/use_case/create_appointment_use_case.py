import i18n

from extensions.appointment.models.appointment import Appointment
from extensions.appointment.models.appointment_event import AppointmentEvent
from extensions.appointment.repository.appointment_repository import (
    AppointmentRepository,
)
from extensions.appointment.router.appointment_requests import (
    CreateAppointmentRequestObject,
)
from extensions.appointment.use_case.base_appointment_use_case import (
    BaseAppointmentUseCase,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from sdk.calendar.service.calendar_service import CalendarService
from sdk.calendar.utils import now_no_seconds
from sdk.common.usecase.response_object import Response
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import utc_str_field_to_val


class CreateAppointmentUseCase(BaseAppointmentUseCase):
    @autoparams()
    def __init__(self, auth_repo: AuthorizationRepository, repo: AppointmentRepository):
        self._auth_repo = auth_repo
        self.repo = repo

    def process_request(self, request_object: CreateAppointmentRequestObject):
        self.preprocess()
        inserted_id = self.repo.create_appointment(request_object)
        key_action_id = self._create_key_action_and_execute(inserted_id)
        request_object.keyActionId = key_action_id
        self.repo.update_appointment(
            appointment_id=inserted_id, appointment=request_object
        )
        return Response(inserted_id)

    def preprocess(self):
        self.set_defaults()

    def set_defaults(self):
        user = self._auth_repo.retrieve_simple_user_profile(
            user_id=self.request_object.userId
        )
        user = AuthorizedUser(user)
        locale = user.get_language()
        self.request_object.title = i18n.t("Appointment.title", locale=locale)
        self.request_object.description = i18n.t("Appointment.body", locale=locale)

    def _create_key_action_and_execute(self, appointment_id: str):
        event: AppointmentEvent = AppointmentEvent.from_dict(
            {
                AppointmentEvent.MODEL: Appointment.__name__,
                AppointmentEvent.TITLE: self.request_object.title,
                AppointmentEvent.DESCRIPTION: self.request_object.description,
                AppointmentEvent.START_DATE_TIME: utc_str_field_to_val(
                    now_no_seconds()
                ),
                AppointmentEvent.END_DATE_TIME: utc_str_field_to_val(
                    self.request_object.startDateTime
                ),
                AppointmentEvent.USER_ID: self.request_object.userId,
                AppointmentEvent.APPOINTMENT_DATE_TIME: self.request_object.startDateTime,
                AppointmentEvent.APPOINTMENT_ID: appointment_id,
                AppointmentEvent.APPOINTMENT_STATUS: self.request_object.status.value,
            }
        )
        event.execute()
        return CalendarService().create_calendar_event(event)
