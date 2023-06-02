from sdk.tests.application_test_utils.test_utils import IntegrationTestCase, SDK_CONFIG_PATH, MIGRATIONS


class SdkTestCase(IntegrationTestCase):
    db_migration_path = MIGRATIONS
    config_file_path = SDK_CONFIG_PATH
