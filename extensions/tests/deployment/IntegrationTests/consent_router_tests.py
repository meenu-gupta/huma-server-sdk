import uuid
from copy import copy

from extensions.deployment.models.consent.consent import Consent
from extensions.tests.deployment.IntegrationTests.deployment_router_tests import (
    AbstractDeploymentTestCase,
)
from extensions.tests.shared.test_helpers import simple_consent


class CreateConsentTestCase(AbstractDeploymentTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(CreateConsentTestCase, cls).setUpClass()
        cls.deployment_id = "5d386cc6ff885918d96edb2c"
        cls.createConsentBody = simple_consent()
        cls.base_path = "/api/extensions/v1beta/deployment"

    def test_consent_creation(self):
        body = self.createConsentBody
        rsp = self.flask_client.post(
            f"{self.base_path}/{self.deployment_id}/consent",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}/consent",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

        # check section_counts
        self.assertEqual(13, len(rsp.json[Consent.SECTIONS]))

        # check additionalConsentQuestions count
        self.assertEqual(2, len(rsp.json[Consent.ADDITIONAL_CONSENT_QUESTIONS]))

    def test_consent_creation_with_id(self):
        body = copy(self.createConsentBody)
        body["id"] = uuid.uuid4()
        rsp = self.flask_client.post(
            f"{self.base_path}/{self.deployment_id}/consent",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_consent_creation_with_date(self):
        body = copy(self.createConsentBody)
        body["createDateTime"] = "2020-04-07T17:05:51"
        rsp = self.flask_client.post(
            f"{self.base_path}/{self.deployment_id}/consent",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_consent_creation_for_not_existing_deployment(self):
        body = copy(self.createConsentBody)
        deployment_id = "5d386cc6ff885918d96edb5c"
        rsp = self.flask_client.post(
            f"{self.base_path}/{deployment_id}/consent", json=body, headers=self.headers
        )
        self.assertEqual(404, rsp.status_code)


class RetrieveConsentTestCase(AbstractDeploymentTestCase):
    def setUp(self):
        super().setUp()
        self.deployment_id = "5d386cc6ff885918d96edb2c"
        self.latest_consent_id = "5e9443789911c97c0b639374"

    def test_latest_consent_retrieve(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}/consent",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(self.latest_consent_id, rsp.json["id"])

    def test_latest_consent_retrieve_deployment_not_exist(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/5d386cc6ff885918d96edc2c/consent",
            headers=self.headers,
        )
        self.assertEqual(404, rsp.status_code)
