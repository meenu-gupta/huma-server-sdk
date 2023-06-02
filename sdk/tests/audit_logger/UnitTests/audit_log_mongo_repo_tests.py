import unittest
from unittest.mock import MagicMock

from sdk.audit_logger.repo.mongo_audit_log_repository import MongoAuditLogRepository


class AuditLogMongoRepoTestCase(unittest.TestCase):
    def test_success_create_audit_log(self):
        data = {"a": "b"}
        db = MagicMock()
        repo = MongoAuditLogRepository(db)
        repo.create_log(data)
        db[repo.AUDIT_LOG_COLLECTION].insert_one.assert_called_with(data)


if __name__ == "__main__":
    unittest.main()
