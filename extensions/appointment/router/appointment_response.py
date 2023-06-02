from extensions.appointment.models.appointment import Appointment
from sdk import convertibleclass
from sdk.common.usecase import response_object
from sdk.common.utils.convertible import required_field


class RetrieveAppointmentsResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        APPOINTMENTS = "appointments"

        appointments: list[Appointment] = required_field()

    def __init__(self, appointments: list[Appointment]):
        value = self.Response.from_dict({self.Response.APPOINTMENTS: appointments})
        super().__init__(value)
