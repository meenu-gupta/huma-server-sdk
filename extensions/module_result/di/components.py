import logging

from extensions.module_result.config.pam_integration_client_config import (
    PAMIntegrationClientConfig,
)
from extensions.module_result.pam.pam_integration_client import PAMIntegrationClient
from extensions.module_result.repository.custom_module_config_repository import (
    CustomModuleConfigRepository,
)
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from extensions.module_result.repository.mongo_custom_module_config_repository import (
    MongoCustomModuleConfigRepository,
)
from extensions.module_result.repository.mongo_module_result_repository import (
    MongoModuleResultRepository,
)
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


def bind_module_result_repository(binder, conf):
    binder.bind_to_provider(
        ModuleResultRepository, lambda: MongoModuleResultRepository()
    )

    logger.debug(f"Module Result Repository bind to Mongo Module Repository")


def bind_custom_module_config_repository(binder, conf):
    binder.bind_to_provider(
        CustomModuleConfigRepository, lambda: MongoCustomModuleConfigRepository()
    )

    logger.debug(f"Module Result Repository bind to Mongo Module Repository")


def bind_pam_integration_client(binder: Binder, config: PhoenixServerConfig):
    module_result_config = config.server.moduleResult

    if not module_result_config:
        return

    client_config: PAMIntegrationClientConfig = module_result_config.pamIntegration
    if not client_config:
        return

    binder.bind("pamIntegrationClient", PAMIntegrationClient(client_config))

    logger.debug(f"pamIntegrationClient bind to PAMIntegrationClient")
