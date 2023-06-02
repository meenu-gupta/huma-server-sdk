from apps.ppserver.tests.shared import APPS_CONFIG_PATH, APPS_MIGRATIONS
from extensions.config.config import ExtensionServerConfig
from sdk.tests.application_test_utils.test_utils import IntegrationTestCase


class AppsTestCase(IntegrationTestCase):
    config_file_path = APPS_CONFIG_PATH
    db_migration_path = APPS_MIGRATIONS
    config_class = ExtensionServerConfig
