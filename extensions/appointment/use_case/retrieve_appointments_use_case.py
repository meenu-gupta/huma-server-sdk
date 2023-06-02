from extensions.appointment.repository.appointment_repository import (
    AppointmentRepository,
)
from extensions.appointment.router.appointment_requests import (
    RetrieveAppointmentsRequestObject,
    RetrieveAppointmentsGetRequestObject,
)
from extensions.appointment.router.appointment_response import (
    RetrieveAppointmentsResponseObject,
)
from extensions.appointment.use_case.base_appointment_use_case import (
    BaseAppointmentUseCase,
)
from sdk.common.usecase.response_object import Response
from sdk.common.utils.inject import autoparams


class RetrieveAppointmentsUseCase(BaseAppointmentUseCase):
    @autoparams()
    def __init__(self, repo: AppointmentRepository):
        self.repo = repo

    def process_request(self, request_object: RetrieveAppointmentsRequestObject):
        appointments = self.repo.retrieve_appointments(
            request_object.userId,
            request_object.requesterId,
            request_object.fromDateTime,
            request_object.toDateTime,
        )
        return Response(appointments)


class RetrieveAppointmentsUseCaseV1(BaseAppointmentUseCase):
    @autoparams()
    def __init__(self, repo: AppointmentRepository):
        self.repo = repo

    def process_request(self, request_object: RetrieveAppointmentsGetRequestObject):
        appointments = self.repo.retrieve_appointments(
            request_object.userId,
            request_object.requesterId,
            skip=request_object.skip,
            limit=request_object.limit,
        )
        return RetrieveAppointmentsResponseObject(appointments)
