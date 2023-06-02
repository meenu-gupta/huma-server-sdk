from pathlib import Path

from extensions.config.config import ExtensionServerConfig
from extensions.tests.shared import EXTENSIONS_CONFIG_PATH, EXTENSIONS_MIGRATIONS
from sdk.tests.application_test_utils.test_utils import IntegrationTestCase


class ExtensionTestCase(IntegrationTestCase):
    config_file_path = EXTENSIONS_CONFIG_PATH
    db_migration_path = EXTENSIONS_MIGRATIONS
    config_class = ExtensionServerConfig
    localization_path = str(Path(__file__).parent.joinpath("shared/localization"))
