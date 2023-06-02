from pymongo.database import Database

from sdk.audit_logger.repo.audit_log_repository import AuditLogRepository
from sdk.common.utils.inject import autoparams


class MongoAuditLogRepository(AuditLogRepository):
    AUDIT_LOG_COLLECTION = "auditlog"

    @autoparams()
    def __init__(self, db: Database):
        self.db = db

    def create_log(self, data: dict) -> str:
        result = self.db[self.AUDIT_LOG_COLLECTION].insert_one(data)
        return str(result.inserted_id)
