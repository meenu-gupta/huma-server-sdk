from unittest.mock import patch, MagicMock

from extensions.publisher.callbacks.publisher_callback import publish_data_task
from extensions.publisher.models.primitive_data import PrimitiveData
from extensions.tests.publisher.IntegrationTests.publisher_router_tests import (
    PublisherRouterTestCase,
)
from extensions.tests.publisher.IntegrationTests.sample_data import (
    sample_event_dict,
    sample_webhook_url,
    sample_expected_webhook_event_json,
    sample_expected_webhook_header,
)


class PublisherTestCase(PublisherRouterTestCase):
    @patch("extensions.publisher.adapters.webhook_adapter.requests.session")
    @patch("extensions.publisher.adapters.kafka_adapter.SerializingProducer")
    def test_publisher_event_webhook_kafka(self, mocked_producer, session_mock):
        request = MagicMock()
        session_mock.return_value = MagicMock(request=request)

        produce = MagicMock()
        mocked_producer.return_value = MagicMock(produce=produce)

        primitive_data = {
            PrimitiveData.USER_ID: sample_event_dict["primitives"][0]["userId"],
            PrimitiveData.NAME: "BloodPressure",
            PrimitiveData.ID: "618a8595a57e07e2de456e33",
        }
        publish_data_task(
            [primitive_data],
            sample_event_dict["moduleId"],
            sample_event_dict["deviceName"],
            sample_event_dict["moduleConfigId"],
            sample_event_dict["deploymentId"],
        )

        # assert that webhook endpoint is called
        request.assert_called_once_with(
            url=sample_webhook_url,
            method="POST",
            headers=sample_expected_webhook_header,
            data=sample_expected_webhook_event_json,
        )

        # assert that kafka produce is called
        produce.assert_called_once()
