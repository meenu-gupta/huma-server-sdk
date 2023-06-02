from extensions.publisher.models.gcp_fhir import GCPFhir
from extensions.publisher.models.publisher import Publisher
from extensions.publisher.models.webhook import Webhook
from extensions.publisher.router.publisher_requests import (
    RetrievePublishersRequestObject,
)
from extensions.tests.publisher.IntegrationTests.publisher_router_tests import (
    PublisherRouterTestCase,
)

DEPLOYMENT_IDS = ["5f652a9661c37dd829c8d23a"]
PUBLISHER_TYPE = Publisher.Target.Type.WEBHOOK.value
EVENT_TYPE = Publisher.Filter.EventType.MODULE_RESULT.value
NAME = "HL7 Integration Publisher New"
DE_IDENTIFIED = False

WEBHOOK = Webhook()
WEBHOOK.endpoint = "https://webhook.site/64a6d6f5-34f3-450c-9497-63ffd468a9e9"
WEBHOOK.authType = "NONE"

GCPFHIR = GCPFhir()
GCPFHIR.url = "https://healthcare.googleapis.com/v1/projects/hu-global-sandbox/locations/us-east4/datasets/test/fhirStores/huma_demo_fhir/fhir"
GCPFHIR.serviceAccountData = "{}"


class PublisherTestCase(PublisherRouterTestCase):
    def test_create_publisher_webhook(self):
        publisher_data = self.get_sample_request_data(
            name=NAME,
            deployment_ids=DEPLOYMENT_IDS,
            publisher_type=PUBLISHER_TYPE,
            event_type=EVENT_TYPE,
            deidentified=DE_IDENTIFIED,
            webhook=WEBHOOK,
        )

        resp = self.flask_client.post(
            self.COMMON_API_URL, headers=self.headers, json=publisher_data
        )
        self.assertEqual(201, resp.status_code)
        self.assertIsNotNone(resp.json["id"])

    def test_create_publisher_gcpfhir(self):
        publisher_data = self.get_sample_request_data(
            name=NAME,
            deployment_ids=DEPLOYMENT_IDS,
            publisher_type=Publisher.Target.Type.GCPFHIR.value,
            event_type=EVENT_TYPE,
            deidentified=DE_IDENTIFIED,
            gcpfhir=GCPFHIR,
        )

        resp = self.flask_client.post(
            self.COMMON_API_URL, headers=self.headers, json=publisher_data
        )
        self.assertEqual(201, resp.status_code)
        self.assertIsNotNone(resp.json["id"])

    def test_create_update_publisher(self):
        publisher_data = self.get_sample_request_data(
            name=NAME,
            deployment_ids=DEPLOYMENT_IDS,
            publisher_type=PUBLISHER_TYPE,
            event_type=EVENT_TYPE,
            deidentified=DE_IDENTIFIED,
            webhook=WEBHOOK,
        )

        resp = self.flask_client.post(
            self.COMMON_API_URL, headers=self.headers, json=publisher_data
        )
        self.assertEqual(201, resp.status_code)
        self.assertIsNotNone(resp.json["id"])

        publisher_id = resp.json["id"]
        publisher_data = self.get_sample_request_data(
            name=NAME,
            deployment_ids=DEPLOYMENT_IDS,
            publisher_type=PUBLISHER_TYPE,
            event_type=EVENT_TYPE,
            deidentified=not DE_IDENTIFIED,
            webhook=WEBHOOK,
        )

        resp = self.flask_client.put(
            self.COMMON_API_URL + "/" + publisher_id,
            headers=self.headers,
            json=publisher_data,
        )
        self.assertEqual(200, resp.status_code)
        self.assertIsNotNone(resp.json["id"])

    def test_create_delete_publisher(self):
        publisher_data = self.get_sample_request_data(
            name=NAME,
            deployment_ids=DEPLOYMENT_IDS,
            publisher_type=PUBLISHER_TYPE,
            event_type=EVENT_TYPE,
            deidentified=DE_IDENTIFIED,
            webhook=WEBHOOK,
        )

        resp = self.flask_client.post(
            self.COMMON_API_URL, headers=self.headers, json=publisher_data
        )
        self.assertEqual(201, resp.status_code)
        self.assertIsNotNone(resp.json["id"])

        publisher_id = resp.json["id"]

        resp = self.flask_client.delete(
            self.COMMON_API_URL + "/" + publisher_id, headers=self.headers
        )
        self.assertEqual(204, resp.status_code)

    def test_delete_publisher(self):
        publisher_id = "61815cb0515a3d3bae2960e7"

        resp = self.flask_client.delete(
            self.COMMON_API_URL + "/" + publisher_id, headers=self.headers
        )
        self.assertEqual(204, resp.status_code)

    def test_create_retrieve_publisher(self):
        publisher_data = self.get_sample_request_data(
            name=NAME,
            deployment_ids=DEPLOYMENT_IDS,
            publisher_type=PUBLISHER_TYPE,
            event_type=EVENT_TYPE,
            deidentified=DE_IDENTIFIED,
            webhook=WEBHOOK,
        )

        resp = self.flask_client.post(
            self.COMMON_API_URL, headers=self.headers, json=publisher_data
        )
        self.assertEqual(201, resp.status_code)
        self.assertIsNotNone(resp.json["id"])

        publisher_id = resp.json["id"]

        resp = self.flask_client.get(
            self.COMMON_API_URL + "/" + publisher_id, headers=self.headers
        )
        self.assertEqual(200, resp.status_code)

        self.assertEqual(resp.json["transform"]["deIdentified"], DE_IDENTIFIED)
        self.assertEqual(resp.json["target"]["retry"], 3)

    def test_retrieve_publishers(self):
        for i in range(15):
            publisher_data = self.get_sample_request_data(
                name=f"{NAME} {i}",
                deployment_ids=DEPLOYMENT_IDS,
                publisher_type=PUBLISHER_TYPE,
                event_type=EVENT_TYPE,
                deidentified=DE_IDENTIFIED,
                webhook=WEBHOOK,
            )

            self.flask_client.post(
                self.COMMON_API_URL, headers=self.headers, json=publisher_data
            )

        # All publishers
        data = {
            RetrievePublishersRequestObject.SKIP: 0,
            RetrievePublishersRequestObject.LIMIT: 10000,
        }
        rsp_data = self._get_successful_response_data(data)

        self.assertNotEqual(0, len(rsp_data["items"]))
        self.assertLess(10, len(rsp_data["items"]))

        # Publishers with skip and limit
        third_publisher_id = rsp_data["items"][2]["id"]
        data = {
            RetrievePublishersRequestObject.SKIP: 2,
            RetrievePublishersRequestObject.LIMIT: 10,
        }
        rsp_data = self._get_successful_response_data(data)

        self.assertNotEqual(0, len(rsp_data["items"]))
        self.assertEqual(10, len(rsp_data["items"]))
        self.assertEqual(third_publisher_id, rsp_data["items"][0]["id"])

    def _get_successful_response_data(self, payload: dict):
        rsp = self.flask_client.post(
            f"{self.COMMON_API_URL}/search", json=payload, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        return rsp.json
