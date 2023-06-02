from extensions.appointment.models.appointment import Appointment
from extensions.appointment.repository.appointment_repository import (
    AppointmentRepository,
)
from extensions.appointment.router.appointment_requests import (
    DeleteAppointmentRequestObject,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.common.policies import are_users_in_the_same_resource
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class DeleteAppointmentUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: AppointmentRepository, auth_repo: AuthorizationRepository):
        self.repo = repo
        self.auth_repo = auth_repo

    def process_request(self, request_object: DeleteAppointmentRequestObject):
        appointment = self.repo.retrieve_appointment(request_object.appointmentId)
        self.check_permission(appointment)
        self.repo.delete_appointment(request_object.appointmentId)
        if appointment.keyActionId:
            CalendarService().delete_calendar_event(appointment.keyActionId)
        return Response()

    def check_permission(self, appointment: Appointment):
        user = self.auth_repo.retrieve_simple_user_profile(user_id=appointment.userId)
        authz_user = AuthorizedUser(user)
        submitter = self.request_object.submitter
        if not are_users_in_the_same_resource(authz_user, submitter):
            raise PermissionDenied
