import logging

from extensions.kardia.models.kardia_integration_config import KardiaIntegrationConfig
from extensions.kardia.repository.kardia_integration_client import (
    KardiaIntegrationClient,
)
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import PhoenixServerConfig

log = logging.getLogger(__name__)


def bind_kardia_integration_client(binder: Binder, config: PhoenixServerConfig):
    module_result_config = config.server.moduleResult

    if not module_result_config:
        return

    kardia_integration_config: KardiaIntegrationConfig = module_result_config.kardia
    if not kardia_integration_config:
        return

    binder.bind(
        KardiaIntegrationClient, KardiaIntegrationClient(kardia_integration_config)
    )

    log.debug(f"kardiaIntegrationClient bind to KardiaIntegrationClient")
