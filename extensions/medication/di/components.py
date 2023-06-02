import logging

from extensions.medication.repository.medication_repository import MedicationRepository
from extensions.medication.repository.mongo_medication_repository import (
    MongoMedicationRepository,
)

logger = logging.getLogger(__name__)


def bind_medication_repository(binder, config):
    binder.bind_to_provider(MedicationRepository, lambda: MongoMedicationRepository())

    logger.debug(f"Medication Repository bind to Mongo Medication Repository")
