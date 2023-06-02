import logging

from extensions.appointment.repository.appointment_repository import (
    AppointmentRepository,
)
from extensions.appointment.repository.mongo_appointment_repository import (
    MongoAppointmentRepository,
)

logger = logging.getLogger(__name__)


def bind_appointment_repository(binder):
    binder.bind_to_provider(AppointmentRepository, lambda: MongoAppointmentRepository())
    logger.debug(f"AppointmentRepository bind to MongoAppointmentRepository")
