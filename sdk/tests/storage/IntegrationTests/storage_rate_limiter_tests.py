from pathlib import Path

from sdk.storage.component import StorageComponent, StorageComponentV1
from sdk.tests.application_test_utils.test_utils import IntegrationTestCase

TEST_RATE_LIMIT_PER_HOUR_READ = 10

VALID_TEST_USER_ID = "5e8f0c74b50aa9656c34789c"


class StorageRateLimiterTestCase(IntegrationTestCase):
    config_file_path = Path(__file__).parent.parent.parent.joinpath(
        "application_test_utils/config.rate-limiter.test.yaml"
    )
    override_config = {
        "server.storage.rateLimit.read": f"{TEST_RATE_LIMIT_PER_HOUR_READ}/minute"
    }
    components = [StorageComponent()]

    def setUp(self):
        self.test_server.rate_limiter.reset()
        super().setUp()
        self.base_url = f"/api/storage/v1beta/signed/url/integrationtests/test.png"

    def test_storage_read_rate_limiter(self):
        for request_number in range(TEST_RATE_LIMIT_PER_HOUR_READ + 1):
            response = self.flask_client.get(self.base_url)
            if request_number != TEST_RATE_LIMIT_PER_HOUR_READ:
                self.assertEqual(401, response.status_code)
            else:
                self.assertEqual(429, response.status_code)


class StorageV1RateLimiterTestCase(IntegrationTestCase):
    config_file_path = Path(__file__).parent.parent.parent.joinpath(
        "application_test_utils/config.rate-limiter.test.yaml"
    )
    override_config = {
        "server.storage.rateLimit.read": f"{TEST_RATE_LIMIT_PER_HOUR_READ}/minute"
    }
    components = [StorageComponentV1()]

    def setUp(self):
        self.test_server.rate_limiter.reset()
        super().setUp()
        self.base_url = f"/api/storage/v1/signed-url/6195da5c41ed7dcd3e3f21aa"

    def test_storage_read_rate_limiter(self):
        for request_number in range(TEST_RATE_LIMIT_PER_HOUR_READ + 1):
            response = self.flask_client.get(self.base_url)
            if request_number != TEST_RATE_LIMIT_PER_HOUR_READ:
                self.assertEqual(401, response.status_code)
            else:
                self.assertEqual(429, response.status_code)
