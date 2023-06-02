from fluent.sender import FluentSender

from sdk.common.adapter.audit_adapter import AuditAdapter
from sdk.phoenix.config.server_config import AuditLogger
from fluent import sender


class FluentdAdapter(AuditAdapter):  # pragma: no cover
    _logger: FluentSender = None

    def __init__(self, audit_logger: AuditLogger, logger: sender.FluentSender):
        self._logger = logger
        self.enable = audit_logger.enable

    def error(self, msg: str, label: str = None, *args, **kwargs):
        if self.enable:
            self._emit("ERROR", msg, label, args, kwargs)

    def info(self, msg: str, label: str = None, *args, **kwargs):
        if self.enable:
            self._emit("INFO", msg, label, args, kwargs)

    def debug(self, msg: str, label: str = None, *args, **kwargs):
        if self.enable:
            self._emit("DEBUG", msg, label, args, kwargs)

    def _emit(self, level: str, msg: str, label: str, args, kwargs):
        if self.enable:
            message = msg.format(args=args)
            self._logger.emit(
                label=label, data={"level": level, "message": message, **kwargs}
            )
