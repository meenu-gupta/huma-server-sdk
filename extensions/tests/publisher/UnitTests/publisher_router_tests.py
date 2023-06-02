import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.publisher.models.publisher import Publisher
from extensions.publisher.router.publisher_router import (
    retrieve_publishers,
    delete_publisher,
    retrieve_publisher,
    create_publisher,
    update_publisher,
)
from extensions.tests.publisher.IntegrationTests.publisher_tests import (
    NAME,
    DEPLOYMENT_IDS,
    DE_IDENTIFIED,
    EVENT_TYPE,
    PUBLISHER_TYPE,
)
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.audit_logger import AuditLog

PUBLISHER_ROUTER_PATH = "extensions.publisher.router.publisher_router"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{PUBLISHER_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch.object(AuditLog, "create_log", MagicMock())
class PublisherRouterTestCase(unittest.TestCase):
    @patch(f"{PUBLISHER_ROUTER_PATH}.jsonify")
    @patch(f"{PUBLISHER_ROUTER_PATH}.CreatePublisherRequestObject")
    @patch(f"{PUBLISHER_ROUTER_PATH}.CreatePublisherUseCase")
    def test_success_create_publisher(self, use_case, req_obj, jsonify):
        payload = {
            Publisher.PUBLISHER_NAME: NAME,
            Publisher.DEPLOYMENT_IDS: DEPLOYMENT_IDS,
            Publisher.DEIDENTIFIED: DE_IDENTIFIED,
            Publisher.INCLUDE_USER_META_DATA: False,
            Publisher.INCLUDE_NULL_FIELDS: False,
            Publisher.EVENT_TYPE: EVENT_TYPE,
            Publisher.PUBLISHER_TYPE: PUBLISHER_TYPE,
        }

        with testapp.test_request_context("/", method="DELETE", json=payload) as _:
            create_publisher()
            req_obj.from_dict.assert_called_with(remove_none_values(payload))
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{PUBLISHER_ROUTER_PATH}.jsonify")
    @patch(f"{PUBLISHER_ROUTER_PATH}.UpdatePublisherRequestObject")
    @patch(f"{PUBLISHER_ROUTER_PATH}.UpdatePublisherUseCase")
    def test_success_update_publisher(self, use_case, req_obj, jsonify):
        publisher_id = SAMPLE_ID
        payload = {
            Publisher.PUBLISHER_NAME: NAME,
            Publisher.DEPLOYMENT_IDS: DEPLOYMENT_IDS,
            Publisher.DEIDENTIFIED: DE_IDENTIFIED,
            Publisher.INCLUDE_USER_META_DATA: False,
            Publisher.INCLUDE_NULL_FIELDS: False,
            Publisher.EVENT_TYPE: EVENT_TYPE,
            Publisher.PUBLISHER_TYPE: PUBLISHER_TYPE,
        }

        with testapp.test_request_context("/", method="DELETE", json=payload) as _:
            update_publisher(publisher_id)
            req_obj.from_dict.assert_called_with(
                {
                    Publisher.ID: publisher_id,
                    **remove_none_values(payload),
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{PUBLISHER_ROUTER_PATH}.DeletePublisherRequestObject")
    @patch(f"{PUBLISHER_ROUTER_PATH}.DeletePublisherUseCase")
    def test_success_delete_publisher(self, use_case, req_obj):
        publisher_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_publisher(publisher_id)
            req_obj.from_dict.assert_called_with({"publisherId": publisher_id})
            use_case().execute.assert_called_with(req_obj.from_dict())

    @patch(f"{PUBLISHER_ROUTER_PATH}.jsonify")
    @patch(f"{PUBLISHER_ROUTER_PATH}.RetrievePublisherRequestObject")
    @patch(f"{PUBLISHER_ROUTER_PATH}.RetrievePublisherUseCase")
    def test_success_retrieve_publisher(self, use_case, req_obj, jsonify):
        publisher_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_publisher(publisher_id)
            req_obj.from_dict.assert_called_with({"publisherId": publisher_id})
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{PUBLISHER_ROUTER_PATH}.jsonify")
    @patch(f"{PUBLISHER_ROUTER_PATH}.RetrievePublishersRequestObject")
    @patch(f"{PUBLISHER_ROUTER_PATH}.RetrievePublishersUseCase")
    def test_success_retrieve_publishers(self, use_case, req_obj, jsonify):
        payload = {"skip": 0, "limit": 10}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            retrieve_publishers()
            req_obj.from_dict.assert_called_with(payload)
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)


if __name__ == "__main__":
    unittest.main()
