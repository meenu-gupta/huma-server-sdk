from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig


def is_flags_enabled():
    config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
    return config.server.deployment.flagsEnabled
