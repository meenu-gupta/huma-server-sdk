import logging

from sdk.storage.repository.storage_repository import StorageRepository
from sdk.storage.repository.mongo_storage_repository import MongoStorageRepository
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


def bind_storage_repository(binder: Binder, config: PhoenixServerConfig):
    binder.bind_to_provider(StorageRepository, lambda: MongoStorageRepository())
    logger.debug(f"StorageRepository bind to MongoStorageRepository")
