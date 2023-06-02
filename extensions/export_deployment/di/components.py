import logging
from pymongo.errors import PyMongoError

from extensions.export_deployment.utils import SourceDatabase, SourceMongoClient
from sdk.common.adapter.mongodb.mongodb_utils import db_is_accessible
from sdk.common.utils import inject
from mongoengine import connect
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.repository.mongo_export_deployment_repository import (
    MongoExportDeploymentRepository,
)
from sdk.common.utils.inject import Binder
from sdk.common.utils.url_utils import clean_password_from_url
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


def bind_export_repositories(binder):
    binder.bind_to_provider(
        ExportDeploymentRepository, lambda: MongoExportDeploymentRepository()
    )
    logger.debug(f"ExportDeployment bind to MongoExportDeploymentRepository")


def bind_source_db_client_and_database(binder: Binder, config: PhoenixServerConfig):
    cfg = config.server.exportDeployment.sourceMongodbDatabase

    mongodb_db_client = connect(
        host=cfg.url, serverSelectionTimeoutMS=10 * 1000, alias="source"
    )

    # testing the connection before connecting
    db = mongodb_db_client[cfg.name]

    safe_url = clean_password_from_url(cfg.url)
    if not db_is_accessible(db):
        raise PyMongoError(f"can not connect source to {safe_url}")

    logger.debug(f"mongodb source client has been connected {safe_url}")
    binder.bind(SourceMongoClient, mongodb_db_client)
    binder.bind_to_provider(
        SourceDatabase, lambda: inject.instance(SourceMongoClient)[cfg.name]
    )
