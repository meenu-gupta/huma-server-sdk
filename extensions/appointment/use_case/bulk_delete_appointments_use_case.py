from extensions.appointment.repository.appointment_repository import (
    AppointmentRepository,
)
from extensions.appointment.router.appointment_requests import (
    BulkDeleteAppointmentsRequestObject,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.common.policies import are_users_in_the_same_resource
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.exceptions.exceptions import InvalidRequestException, PermissionDenied
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class BulkDeleteAppointmentsUseCase(UseCase):
    request_object: BulkDeleteAppointmentsRequestObject

    @autoparams()
    def __init__(self, repo: AppointmentRepository, auth_repo: AuthorizationRepository):
        self.repo = repo
        self.auth_repo = auth_repo

    def process_request(self, request_object: BulkDeleteAppointmentsRequestObject):
        self.check_permission()

        appointments = self.repo.retrieve_appointments_by_ids(
            request_object.appointmentIds
        )
        are_all_appointments_for_the_user = all(
            appointment.userId == request_object.userId for appointment in appointments
        )
        if not are_all_appointments_for_the_user:
            msg = f"All of the appointments in request should be for user #{request_object.userId}"
            raise InvalidRequestException(msg)

        deleted_appointments_count = self.repo.bulk_delete_appointments(
            request_object.appointmentIds
        )
        key_action_ids = [
            appointment.keyActionId
            for appointment in appointments
            if appointment.keyActionId
        ]
        CalendarService().batch_delete_calendar_events_by_ids(key_action_ids)
        return Response({"deletedAppointments": deleted_appointments_count})

    def check_permission(self):
        user = self.auth_repo.retrieve_simple_user_profile(
            user_id=self.request_object.userId
        )
        authz_user = AuthorizedUser(user)
        submitter = self.request_object.submitter
        if not are_users_in_the_same_resource(authz_user, submitter):
            raise PermissionDenied
