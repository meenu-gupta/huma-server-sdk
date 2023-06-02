import unittest
from unittest.mock import MagicMock

from bson import ObjectId

from extensions.publisher.models.publisher import Publisher
from extensions.publisher.models.webhook import Webhook
from extensions.publisher.router.publisher_requests import (
    CreatePublisherRequestObject,
    UpdatePublisherRequestObject,
    RetrievePublishersRequestObject,
    RetrievePublisherRequestObject,
    DeletePublisherRequestObject,
)
from extensions.publisher.use_case.publisher_use_case import (
    CreatePublisherUseCase,
    UpdatePublisherUseCase,
    RetrievePublisherUseCase,
    DeletePublisherUseCase,
    RetrievePublishersUseCase,
)

DEPLOYMENT_IDS = ["5f652a9661c37dd829c8d23a"]
ID = "619425abc3c1cd96eac8ba24"
PUBLISHER_TYPE = "WEBHOOK"
LISTENER_TYPE = "DEPLOYMENT_IDS"
EVENT_TYPE = "MODULE_RESULT"
NAME = "HL7 Integration Publisher New"
DE_IDENTIFIED = False
WEBHOOK = Webhook()
WEBHOOK.endpoint = "https://webhook.site/64a6d6f5-34f3-450c-9497-63ffd468a9e9"
WEBHOOK.authType = "NONE"


class PublisherTestCase(unittest.TestCase):
    @staticmethod
    def test_create_publisher_use_case_valid():
        request_data = {
            Publisher.PUBLISHER_NAME: NAME,
            Publisher.PUBLISHER_TRANSFORM: {
                Publisher.INCLUDE_USER_META_DATA: False,
                Publisher.INCLUDE_NULL_FIELDS: False,
                Publisher.DEIDENTIFIED: DE_IDENTIFIED,
            },
            Publisher.PUBLISHER_TARGET: {
                Publisher.PUBLISHER_TYPE: PUBLISHER_TYPE,
                Publisher.WEBHOOK: WEBHOOK,
            },
            Publisher.PUBLISHER_FILTER: {
                Publisher.DEPLOYMENT_IDS: DEPLOYMENT_IDS,
                Publisher.EVENT_TYPE: EVENT_TYPE,
                Publisher.LISTENER_TYPE: LISTENER_TYPE,
            },
        }

        request_object = CreatePublisherRequestObject.from_dict(request_data)
        mocked_publisher_repo = MagicMock()
        mocked_publisher_repo.create_publisher.return_value = str(ObjectId())
        use_case = CreatePublisherUseCase(mocked_publisher_repo)
        use_case.execute(request_object)
        mocked_publisher_repo.create_publisher.assert_called_with(request_object)

    @staticmethod
    def test_update_publisher_use_case_valid():
        request_data = {
            Publisher.ID: ID,
            Publisher.PUBLISHER_NAME: NAME,
            Publisher.PUBLISHER_TRANSFORM: {
                Publisher.INCLUDE_USER_META_DATA: False,
                Publisher.INCLUDE_NULL_FIELDS: False,
                Publisher.DEIDENTIFIED: DE_IDENTIFIED,
            },
            Publisher.PUBLISHER_TARGET: {
                Publisher.PUBLISHER_TYPE: PUBLISHER_TYPE,
                Publisher.WEBHOOK: WEBHOOK,
            },
            Publisher.PUBLISHER_FILTER: {
                Publisher.DEPLOYMENT_IDS: DEPLOYMENT_IDS,
                Publisher.EVENT_TYPE: EVENT_TYPE,
                Publisher.LISTENER_TYPE: LISTENER_TYPE,
            },
        }

        request_object = UpdatePublisherRequestObject.from_dict(request_data)
        mocked_publisher_repo = MagicMock()
        use_case = UpdatePublisherUseCase(mocked_publisher_repo)
        use_case.execute(request_object)
        mocked_publisher_repo.update_publisher.assert_called_with(request_object)

    @staticmethod
    def test_delete_publisher_use_case_valid():
        publisher_id = "61815cb0515a3d3bae2960e7"
        request_object = DeletePublisherRequestObject.from_dict(
            {"publisherId": publisher_id}
        )

        mocked_publisher_repo = MagicMock()
        use_case = DeletePublisherUseCase(mocked_publisher_repo)
        use_case.execute(request_object)
        mocked_publisher_repo.delete_publisher.assert_called_with(
            request_object.publisherId
        )

    @staticmethod
    def test_retrieve_publisher_use_case_valid():
        publisher_id = "61815cb0515a3d3bae2960e7"

        request_object = RetrievePublisherRequestObject.from_dict(
            {"publisherId": publisher_id}
        )
        mocked_publisher_repo = MagicMock()
        use_case = RetrievePublisherUseCase(mocked_publisher_repo)
        use_case.execute(request_object)
        mocked_publisher_repo.retrieve_publisher.assert_called_with(
            request_object.publisherId
        )

    @staticmethod
    def test_retrieve_publishers_use_case_valid():
        payload = {"skip": 0, "limit": 10}

        request_object = RetrievePublishersRequestObject().from_dict(payload)

        mocked_publisher_repo = MagicMock()
        mocked_publisher_repo.retrieve_publishers.return_value = ([], 0)

        RetrievePublishersUseCase(mocked_publisher_repo).execute(request_object)

        mocked_publisher_repo.retrieve_publishers.assert_called_with(skip=0, limit=10)


if __name__ == "__main__":
    unittest.main()
