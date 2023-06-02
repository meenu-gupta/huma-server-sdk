import logging

from extensions.dashboard.repository.dashobard_repository import DashboardRepository
from extensions.dashboard.repository.mongo_dashboard_repository import (
    MongoDashboardRepository,
)

logger = logging.getLogger(__name__)


def bind_dashboard_repository(binder):
    binder.bind_to_provider(DashboardRepository, lambda: MongoDashboardRepository())
    logger.debug(f"DashboardRepository bind to MongoDashboardRepository")
