from extensions.appointment.models.appointment import Appointment
from extensions.appointment.repository.appointment_repository import (
    AppointmentRepository,
)
from extensions.authorization.events.get_badges_event import GetUserBadgesEvent
from sdk.common.utils.inject import autoparams


@autoparams("repo")
def get_appointment_badge(event: GetUserBadgesEvent, repo: AppointmentRepository):
    appointments_count = repo.retrieve_pending_appointment_count(event.user_id)
    return {"appointments": appointments_count}
