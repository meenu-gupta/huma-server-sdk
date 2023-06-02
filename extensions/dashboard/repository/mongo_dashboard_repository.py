from pymongo.database import Database

from extensions.dashboard.repository.dashobard_repository import DashboardRepository
from sdk.common.utils.inject import autoparams


class MongoDashboardRepository(DashboardRepository):
    DASHBOARD_COLLECTION = "dashboard"
    GADGET_COLLECTION = "gadget"
    IGNORED_FIELDS = ()

    @autoparams()
    def __init__(self, database: Database):
        self._db = database
