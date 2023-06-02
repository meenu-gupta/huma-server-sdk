import logging

from sdk.audit_logger.adapter.audit_log_adapter import AuditLogAdapter
from sdk.audit_logger.repo.audit_log_repository import AuditLogRepository
from sdk.audit_logger.repo.mongo_audit_log_repository import MongoAuditLogRepository
from sdk.common.adapter.audit_adapter import AuditAdapter

logger = logging.getLogger(__name__)


def bind_audit_logger_repository(binder, conf):
    binder.bind_to_provider(AuditLogRepository, lambda: MongoAuditLogRepository())

    logger.debug(
        "AuditLogRepository Repository bind to MongoAuditLogRepository Repository"
    )


def bind_audit_adapter(binder, config):
    audit_adapter = AuditLogAdapter(config.server.auditLogger)
    binder.bind(AuditAdapter, audit_adapter)

    logger.debug(f"AuditAdapter is configured")
