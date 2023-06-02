import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError

here = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(here, "../..")))

from extensions.config.config import ExtensionServerConfig
from sdk.common.mongodb_migrations.config import Configuration
from sdk.common.mongodb_migrations.migration_manager import MigrationManager
from sdk.common.utils.url_utils import clean_password_from_url

logger = logging.getLogger("migrate.py")


def migrate(path: str, dotenv_path: str, config: str, loglevel: str = logging.INFO):
    """
    A small utility to manually apply migrations to mongoDB.
    use `$python migrate.py --help` for details
    """
    logging.basicConfig(level=loglevel)
    dotenv_path = os.path.join(here, dotenv_path)
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    config_path = os.path.join(here, config)
    config = ExtensionServerConfig.get(config_path, {})

    migration_path = os.path.join(here, path)
    cfg = config.server.adapters.mongodbDatabase
    try:
        migration_config = Configuration.config_factory(
            cfg.url, cfg.name, cfg.metaStore, migration_path, cfg.processName
        )
        MigrationManager(migration_config).run()
    except DuplicateKeyError as e:
        logger.info("Migration is progressing on other process")
        logger.info(f"Details: {str(e.details)}")
    except Exception as e:
        logger.info(f"Failed to apply migration {str(e)}")
        logger.info(f"Details: {str(sys.exc_info()[0])}")

    logger.debug(
        f"running migration has been connected {clean_password_from_url(cfg.url)}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migration manager CLI")
    parser.add_argument(
        "-c", "--config", type=str, help="yaml config path", default="config.dev.yaml"
    )
    parser.add_argument(
        "--dotenv", type=str, help="dotenv file path", default="dev.env"
    )
    parser.add_argument(
        "-p", "--path", type=str, help="migrations folder path", default="migrations"
    )
    parser.add_argument(
        "-l", "--loglevel", type=str, help="logging level", default=logging.INFO
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    migrate(args.path, args.dotenv, args.config, args.loglevel)
