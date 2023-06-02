from dataclasses import field

from sdk.common.utils.convertible import convertibleclass, required_field, default_field


@convertibleclass
class MongodbDatabaseConfig:
    name: str = required_field()
    url: str = default_field()
    metaStore: str = field(default="_databasemigration")
    migrationsFolderPath: str = field(default="migrations")
    processName: str = field(default="phoenix_server")
