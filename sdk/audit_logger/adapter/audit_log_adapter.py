from sdk.common.adapter.audit_adapter import AuditAdapter
from sdk.audit_logger.repo.audit_log_repository import AuditLogRepository
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import AuditLogger


class AuditLogAdapter(AuditAdapter):
    def __init__(self, audit_logger: AuditLogger):
        self.enable = audit_logger.enable

    def error(self, msg: str, label: str = None, *args, **kwargs):
        self._emit("ERROR", msg, label, args, kwargs)

    def info(self, msg: str, label: str = None, *args, **kwargs):
        self._emit("INFO", msg, label, args, kwargs)

    def debug(self, msg: str, label: str = None, *args, **kwargs):
        self._emit("DEBUG", msg, label, args, kwargs)

    def _emit(self, level: str, msg: str, label: str, args, kwargs):
        message = msg.format(args=args)
        if self.enable:
            repo = inject.instance(AuditLogRepository)
            repo.create_log(
                {"label": label, "level": level, "message": message, **kwargs}
            )
