import logging

from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.repository.mongo_auth_repository import MongoAuthRepository
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


def bind_auth_repository(binder: Binder, config: PhoenixServerConfig):
    binder.bind_to_provider(AuthRepository, lambda: MongoAuthRepository())
    logger.debug(f"AuthRepository bind to MongoAuthRepository")
