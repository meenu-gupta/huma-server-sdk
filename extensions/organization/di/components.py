import logging

from extensions.organization.repository.mongo_organization_repository import (
    MongoOrganizationRepository,
)
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)

logger = logging.getLogger(__name__)


def bind_organization_repository(binder, conf):
    binder.bind_to_provider(
        OrganizationRepository, lambda: MongoOrganizationRepository()
    )

    logger.debug("Organization Repository bind to Mongo Organization Repository")
