from pathlib import Path
from unittest.mock import patch

from requests import Response

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.kardia.component import KardiaComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent

USER_ID = "5e84b0dab8dfa268b1180536"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
SAMPLE_ID = "5e84b0dab8dfa268b1180aaa"


class KardiaTest(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        KardiaComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]

    def setUp(self):
        super().setUp()

        self.headers = self.get_headers_for_token(USER_ID)
        self.base_route = "/api/extensions/v1beta/kardia"

    @patch("extensions.kardia.repository.kardia_integration_client.requests")
    def test_create_kardia_patient(self, mock_requests):
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_ID}", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertIsNone(rsp.json.get("kardiaId"))

        mock_requests.post.side_effect = self.post_side_effect

        email = "test@huma.com"
        dob = "1970-02-01"
        rsp = self.flask_client.post(
            f"{self.base_route}/patient/{USER_ID}",
            json={"email": email, "dob": dob},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

        self.assertEqual(email, rsp.json["email"])
        self.assertEqual(dob, rsp.json["dob"])

        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_ID}", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertIsNotNone(rsp.json.get("kardiaId"))

    def test_sync_kardia_data_no_kardia_id(self):
        rsp = self.flask_client.get(
            f"{self.base_route}/sync/{USER_ID}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

        self.assertEqual([], rsp.json)

    @patch("extensions.kardia.repository.kardia_integration_client.requests")
    def test_sync_kardia_data_success(self, mock_requests):
        mock_requests.post.side_effect = self.post_side_effect
        mock_requests.get.side_effect = self.get_side_effect

        # create karida patient to populate kardiaId under user profile
        rsp = self.flask_client.post(
            f"{self.base_route}/patient/{USER_ID}",
            json={"email": "email", "dob": "dob"},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_route}/sync/{USER_ID}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

        ecg_record = rsp.json[0]
        self.assertEqual(USER_ID, ecg_record["userId"])
        self.assertEqual("ECGAliveCor", ecg_record["moduleId"])
        self.assertEqual(SAMPLE_ID, ecg_record["kardiaEcgRecordId"])

        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_ID}/module-result/ECGAliveCor/search",
            json={},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

    def post_side_effect(self, *args, **kwargs):
        response = Response()
        response.status_code = 200

        (url,) = args
        if "v1/patients" in url:
            response._content = b'{"id": "wNSEDeLOEPQE5rznkJmwbnjpxfdst93i", "mrn": "JS-20000721", "dob": "1970-02-01", "email": "test@huma.com", "firstname": "Joe", "lastname": "Smith", "sex": 1}'
        elif "v1/users" in url:
            response._content = b'{"requestId": "q1ATFmh7OShS2Dmd1cVAb6boqkrp7gif"}'

        return response

    def get_side_effect(self, *args, **kwargs):
        response = Response()
        response.status_code = 200

        (url,) = args
        if ".pdf" in url:
            response._content = b"file content"
        elif "recordings" in url:
            response._content = b'{"totalCount": 200, "recordings": [{"id": "5e84b0dab8dfa268b1180aaa", "patientID": "wNSEDeLOEPQE5rznkJmwbnjpxfdst93i", "algorithmDetermination": "normal", "duration": 30000, "heartRate": 65, "note": "Drank coffee, having palpitations.", "recordedAt": "2008-09-15T15:53:00+05:00"}], "pageInfo": {"startCursor": "c3RhcnRDdXJzb3I=", "endCursor": "ZW5kQ3Vyc29yc2Rh=", "hasNextPage": true}}'

        return response
