import logging
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime

import pymongo
from pymongo.database import Database

from sdk.common.mongodb_migrations.config import Configuration, Execution

logger = logging.getLogger("MigrationManager")


class MigrationManager(object):
    config: Configuration = None
    db: Database = None
    migrations: dict[str, str] = {}
    database_migration_names: list[str] = None

    def __init__(self, config: Configuration = None):
        self.config = config or Configuration()

    def run(self):
        self.db = self._get_mongo_database(
            self.config.mongo_host,
            self.config.mongo_port,
            self.config.mongo_database,
            self.config.mongo_username,
            self.config.mongo_password,
            self.config.mongo_url,
        )
        logger.info(
            f"searching for migration files in folder {self.config.mongo_migrations_path}"
        )
        files = os.listdir(self.config.mongo_migrations_path)
        for file in files:
            result = re.match(r"^(\d+)[_a-z]*\.py$", file)
            if result:
                self.migrations[result.group(1)] = file[:-3]
        database_migrations = self._get_migration_names()
        self.database_migration_names = [
            migration["migration_datetime"] for migration in database_migrations
        ]
        if set(self.database_migration_names) - set(self.migrations.keys()):
            logger.warning("migrations doesn't match")
            sys.exit(1)
        if self.database_migration_names:
            logger.info(
                "Found previous migrations, last migration is version: %s"
                % self.database_migration_names[0]
            )
        else:
            logger.info("No previous migrations found")
        sys.path.insert(0, self.config.mongo_migrations_path)
        {Execution.MIGRATE: self._do_migrate, Execution.DOWNGRADE: self._do_rollback}[
            self.config.execution
        ]()

    def _do_migrate(self):
        if len(self.migrations.keys()) <= 0:
            return

        for migration_datetime in sorted(self.migrations.keys()):
            should_migrate = (
                not self.database_migration_names
                or migration_datetime > self.database_migration_names[0]
            )
            if not should_migrate:
                continue

            self._apply_migration(
                self.migrations[migration_datetime], migration_datetime
            )

    def _apply_migration(self, migration: str, code: str):
        logger.info(f"Trying to upgrade version: {migration}")
        module = __import__(migration)
        with self._db_lock(expires_in=module.Migration.max_db_lock_ttl):
            migration_object = module.Migration(
                host=self.config.mongo_host,
                port=self.config.mongo_port,
                database=self.config.mongo_database,
                user=self.config.mongo_username,
                password=self.config.mongo_password,
                url=self.config.mongo_url,
            )

            try:
                migration_object.upgrade()
            except Exception as error:
                logger.warning(
                    f"Failed to upgrade version: {migration}\n"
                    + f"More details: {str(error)}"
                )
                raise error

            logger.info(f"Succeed to upgrade version: {migration}")
            self._create_migration_record(code)

    def _do_rollback(self):
        for migration_datetime in sorted(self.database_migration_names, reverse=True):
            path = self.migrations[migration_datetime]
            if not path:
                continue

            module = __import__(path)
            with self._db_lock(expires_in=module.Migration.max_db_lock_ttl):
                logger.info(f"Trying to downgrade version: {path}")
                try:
                    migration_object = module.Migration(
                        host=self.config.mongo_host,
                        port=self.config.mongo_port,
                        database=self.config.mongo_database,
                        user=self.config.mongo_username,
                        password=self.config.mongo_password,
                        url=self.config.mongo_url,
                    )
                    migration_object.downgrade()
                except Exception as error:
                    logger.info(f"Failed to downgrade version: {path}")
                    logger.info(error.__class__)
                    if hasattr(error, "message"):
                        logger.info(error.message)
                    raise error

                logger.info(f"Succeed to downgrade version: {path}")
                self._remove_migration(migration_datetime)

    def _get_migration_names(self):
        return (
            self.db[self.config.metastore]
            .find()
            .sort("migration_datetime", pymongo.DESCENDING)
        )

    def _create_migration_record(self, code: str):
        self.db[self.config.metastore].insert_one(
            {"migration_datetime": code, "created_at": datetime.now()}
        )

    def _remove_migration(self, migration_datetime):
        self.db[self.config.metastore].remove(
            {"migration_datetime": migration_datetime}
        )

    def _get_mongo_database(self, host, port, database, user, password, url):
        if url and database is not None:
            client = pymongo.MongoClient(url)
            return client.get_database(database)

        else:
            raise Exception("no database, url or auth_database in url provided")

    @contextmanager
    def _db_lock(self, expires_in: int):
        lock_collection = self.db.get_collection("_lock")
        lock_collection.drop_index("updated_1")
        lock_collection.create_index("updated", expireAfterSeconds=expires_in)
        lock_collection.insert_one(
            {
                "_id": self.config.process_name,
                "acquirer": self.config.process_name,
                "updated": datetime.utcnow(),
            }
        )

        try:
            yield
        finally:
            lock_collection = self.db.get_collection("_lock")
            lock_collection.delete_one({"_id": self.config.process_name})
