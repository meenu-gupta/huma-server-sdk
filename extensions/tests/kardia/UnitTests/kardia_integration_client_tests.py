import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

from extensions.kardia.repository.kardia_integration_client import (
    KardiaIntegrationClient,
)

KARDIA_CLIENT_PATH = "extensions.kardia.repository.kardia_integration_client"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


class KardiaIntegrationClientTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.config = MagicMock()
        self.client = KardiaIntegrationClient(self.config)

    @patch(f"{KARDIA_CLIENT_PATH}.random")
    @patch(f"{KARDIA_CLIENT_PATH}.json")
    @patch(f"{KARDIA_CLIENT_PATH}.requests")
    @patch(f"{KARDIA_CLIENT_PATH}.g")
    def test_success_create_kardia_patient(self, g_mock, requests, json, random):
        g_mock.user = MagicMock()
        random.choice.return_value = "a"
        email = "user@huma.com"
        dob = "10/10/2010"
        self.client.create_kardia_patient(email, dob)
        data = {
            "email": email,
            "password": "a" * 12,
            "countryCode": "us",
            "patientId": json.loads().get(),
        }
        requests.post.assert_called_with(
            self.config.baseUrl.__add__(), auth=(self.config.apiKey, ""), data=data
        )

    @patch(f"{KARDIA_CLIENT_PATH}.json")
    @patch(f"{KARDIA_CLIENT_PATH}.requests")
    def test_success_retrieve_patient_recordings(self, requests, json):
        patient_id = SAMPLE_ID
        self.client.retrieve_patient_recordings(patient_id)
        requests.get.assert_called_with(
            self.config.baseUrl.__add__().__add__().__add__(),
            auth=(self.config.apiKey, ""),
        )

    @patch(f"{KARDIA_CLIENT_PATH}.json")
    @patch(f"{KARDIA_CLIENT_PATH}.requests")
    def test_success_retrieve_single_ecg(self, requests, json):
        record_id = SAMPLE_ID
        self.client.retrieve_single_ecg(record_id)
        requests.get.assert_called_with(
            self.config.baseUrl.__add__().__add__(),
            auth=(self.config.apiKey, ""),
        )

    @patch(f"{KARDIA_CLIENT_PATH}.requests")
    def test_success_retrieve_single_ecg_pdf(self, requests):
        record_id = SAMPLE_ID
        self.client.retrieve_single_ecg_pdf(record_id)
        requests.get.assert_called_with(
            self.config.baseUrl.__add__().__add__().__add__(),
            auth=(self.config.apiKey, ""),
        )


if __name__ == "__main__":
    unittest.main()
