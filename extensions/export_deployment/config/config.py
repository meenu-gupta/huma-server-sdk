from dataclasses import field

from sdk.common.adapter.mongodb.mongodb_config import MongodbDatabaseConfig
from sdk.common.utils.convertible import convertibleclass, default_field
from sdk.phoenix.config.server_config import BasePhoenixConfig


@convertibleclass
class ExportDeploymentConfig(BasePhoenixConfig):
    sourceMongodbDatabase: MongodbDatabaseConfig = default_field()
    summaryReportEnabled: bool = field(default=True)
