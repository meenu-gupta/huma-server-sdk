from pathlib import Path

from extensions.tests.publisher.IntegrationTests.publisher_router_tests import (
    PublisherRouterTestCase,
)


class PublisherTestCase(PublisherRouterTestCase):
    config_file_path = Path(__file__).with_name("config.test.yaml")

    def test_disabled_publisher_component(self):
        publisher_id = "61815cb0515a3d3bae2960e7"

        resp = self.flask_client.delete(
            self.COMMON_API_URL + "/" + publisher_id, headers=self.headers
        )
        self.assertEqual(404, resp.status_code)
