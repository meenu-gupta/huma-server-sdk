from extensions.appointment.repository.appointment_repository import (
    AppointmentRepository,
)
from extensions.appointment.router.appointment_requests import (
    RetrieveAppointmentRequestObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrieveAppointmentUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: AppointmentRepository):
        self.repo = repo

    def process_request(self, request_object: RetrieveAppointmentRequestObject):
        appointment = self.repo.retrieve_appointment(request_object.appointmentId)
        return Response(appointment)
