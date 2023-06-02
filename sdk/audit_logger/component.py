from sdk.audit_logger.config.config import AuditLoggerConfig
from sdk.audit_logger.di.components import (
    bind_audit_logger_repository,
    bind_audit_adapter,
)
from sdk.common.utils.inject import Binder
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig


class AuditLoggerComponent(PhoenixBaseComponent):
    config_class = AuditLoggerConfig
    tag_name = "auditLogger"

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_audit_logger_repository(binder, config)

        bind_audit_adapter(binder, config)
