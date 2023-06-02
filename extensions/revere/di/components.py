import logging

from extensions.revere.repository.mongo_revere_repository import (
    MongoRevereTestRepository,
)
from extensions.revere.repository.revere_repository import RevereTestRepository

logger = logging.getLogger(__name__)


def bind_revere_repository(binder, conf):
    binder.bind_to_provider(RevereTestRepository, lambda: MongoRevereTestRepository())

    logger.debug(f"Revere Repository bind to Mongo Revere Repository")
