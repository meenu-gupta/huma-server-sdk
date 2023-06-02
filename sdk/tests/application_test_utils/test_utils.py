import logging
import os
import sys
import warnings
from pathlib import Path
from unittest import TestCase

from flask import Flask
from flask.testing import FlaskClient
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from redis import Redis

from sdk.common.adapter.mocked_push_adapter import MockedPushAdapter
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.mongodb_migrations.config import Configuration
from sdk.common.mongodb_migrations.migration_manager import MigrationManager
from sdk.common.utils import inject
from sdk.common.utils.file_utils import load_mongo_dump_file
from sdk.phoenix.component_manager import PhoenixComponentManager, PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.server import PhoenixServer
from sdk.tests.application_test_utils.comparator import assert_matches

SDK_CONFIG_PATH = Path(__file__).with_name("config.test.yaml")
MIGRATIONS = str(Path(__file__).parent.parent.joinpath("migrations"))
USER_ID = "5e8f0c74b50aa9656c34789c"

_DEFAULTS = {
    "MP_MONGODB_URL": "mongodb://root:password123@localhost:27027",
    "MP_SOURCE_MONGODB_URL": "mongodb://root:password123@localhost:27027",
    "MP_REDIS_URL": "redis://default:redispassword@localhost:6389",
    "MP_MINIO_URL": "localhost:9005",
    "MP_MINIO_BASE_URL": "http://localhost:9005",
    "MP_MINIO_ACCESS_KEY": "minio",
    "MP_MINIO_SECRET_KEY": "minio123",
    "MP_APNS_TOPIC": "com.huma.apns-testing",
    "MP_APNS_CERT_PATH": "apps/ppserver/apns.crt.pem",
    "MP_APNS_KEY_PATH": "apps/ppserver/apns.key.pem",
    "MP_FROM_EMAIL": "test@medopad.com",
}

logger = logging.getLogger(__name__)

for default in _DEFAULTS.keys():
    if default not in os.environ:
        os.environ[default] = _DEFAULTS[default]


class IntegrationTestCase(TestCase):
    db_migration_path: str = None
    fixtures: list[str]
    test_app: Flask
    flask_client: FlaskClient
    mongo_client: MongoClient
    mongo_database: Database
    config: PhoenixServerConfig
    components: list
    config_file_path: str
    override_config: dict = None
    localization_path = str(Path(__file__).parent.joinpath("test_localization"))
    config_class = PhoenixServerConfig

    @classmethod
    def setUpClass(cls) -> None:
        super(IntegrationTestCase, cls).setUpClass()
        cls.test_server = cls.set_test_phoenix_server(
            db_migration_path=cls.db_migration_path,
            config_file_path=cls.config_file_path,
            components=cls.components,
            override_config=cls.override_config,
        )
        cls.set_test_app(inject.instance(Flask))

        cls.test_app.config["TESTING"] = True
        cls.test_app.config["DEBUG"] = True
        cls.test_app.config["PROPAGATE_EXCEPTIONS"] = False
        cls.flask_client = cls.test_app.test_client()

        # mock adapters
        inject.get_injector().rebind(
            lambda binder: binder.bind("fcmPushAdapter", MockedPushAdapter())
            .bind("apnsPushAdapter", MockedPushAdapter())
            .bind("twilioPushAdapter", MockedPushAdapter())
            .bind("aliCloudPushAdapter", MockedPushAdapter())
        )

    def assertEmpty(self, container):
        self.assertEqual(0, len(container))

    @classmethod
    def set_test_mongo_database(cls, config: PhoenixServerConfig):
        url = config.server.adapters.mongodbDatabase.url
        cls.database_name = config.server.adapters.mongodbDatabase.name

        cls.config = config
        cls.mongo_client = MongoClient(url)
        cls.mongo_database = cls.mongo_client.get_database(cls.database_name)
        cls.mongo_database["_databasemigration"].delete_many({})

    def set_test_redis_database(self, config: PhoenixServerConfig):
        url = config.server.adapters.redisDatabase.url

        self.redis_client = Redis.from_url(url)
        self.redis_client.flushall()

    @classmethod
    def set_test_phoenix_server(
        cls,
        config_file_path: str,
        db_migration_path: str = None,
        components: list[PhoenixBaseComponent] = None,
        override_config: dict = None,
    ) -> PhoenixServer:
        cfg = cls.config_class.get(config_file_path, override_config)
        # set db before setting up server
        cls.set_test_mongo_database(cfg)
        cls.apply_migration(db_migration_path, cfg)
        # register components with manager
        component_manager = PhoenixComponentManager()
        component_manager.register_components(components)
        return PhoenixServer(
            config=cfg,
            component_manager=component_manager,
            testing=True,
            localization_path=cls.localization_path,
        )

    @classmethod
    def set_test_app(cls, app):
        warnings.filterwarnings(
            action="ignore", message="unclosed", category=ResourceWarning
        )
        for route_name, callbacks in app.before_request_funcs.items():
            existing_names = set()
            temp_list = []
            for callback in callbacks:
                if callback.__name__ not in existing_names:
                    temp_list.append(callback)
                    existing_names.add(callback.__name__)

            app.before_request_funcs[route_name] = temp_list
        cls.test_app = app
        # for jwt token
        ctx = app.app_context()
        ctx.push()

    def setUp(self):
        for collection in self.mongo_database.list_collection_names():
            if collection.startswith("_"):
                continue
            self.mongo_database[collection].delete_many({})

        if hasattr(self, "fixtures") and self.fixtures:
            for fixture in self.fixtures:
                load_mongo_dump_file(str(fixture), self.mongo_database)

    def tearDown(self):
        """
        might be useful one day:

        from platform_play.shared.providers import provides_gremlin_driver
        gremlin_driver = provides_gremlin_driver()
        gremlin_driver.close()
        provides_gremlin_driver.cache_clear()

        """
        super().tearDown()

    @staticmethod
    def create_token(identity):
        user_claims = {"projectId": "ptest1", "clientId": "ctest1"}
        return inject.instance(TokenAdapter).create_access_token(
            identity=identity, user_claims=user_claims
        )

    @staticmethod
    def create_refresh_token(identity, user_claims=None):
        return inject.instance(TokenAdapter).create_refresh_token(
            identity=identity, user_claims=user_claims
        )

    @staticmethod
    def get_headers_for_token(identity=USER_ID):
        token = IntegrationTestCase.create_token(identity)
        return {"Authorization": "Bearer {}".format(token)}

    @classmethod
    def apply_migration(
        cls, path: str, config: PhoenixServerConfig, force_apply: bool = False
    ):
        cfg = config.server.adapters.mongodbDatabase
        if force_apply:
            cls.mongo_database[cfg.metaStore].delete_many({})
        try:
            migration_config = Configuration.config_factory(
                cfg.url, cfg.name, cfg.metaStore, path, cfg.processName
            )
            MigrationManager(migration_config).run()
        except DuplicateKeyError:
            logger.info("Migration is progressing on other process")
        except Exception as e:
            logger.info(f"Failed to apply migration {str(e)}")
            logger.info(f"Details: {str(sys.exc_info()[0])}")

    def assert_matches(self, expected, actual):
        assert_matches(expected, actual)
