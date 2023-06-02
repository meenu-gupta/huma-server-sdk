from pathlib import Path

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.exceptions import UserErrorCodes
from extensions.module_result.modules import MedicationsModule
from extensions.medication.component import MedicationComponent
from extensions.medication.models.medication import Medication
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent

VALID_USER_ID = "5e84b0dab8dfa268b1180536"
INVALID_USER_ID = "6e84b0dab8dfa268b1180532"
VALID_MANAGER_ID = "5e8f0c74b50aa9656c34789d"
VALID_SUPER_ADMIN_ID = "5e8f0c74b50aa9656c34789b"
USER_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"

VALID_MEDICATION_ID = "5eafd121b2d79d48ce4cd9e8"
INVALID_MEDICATION_ID = "2e8cc88d0e8f49bbe59d11ba"

MEDICATION_COLLECTION = "medication"


def simple_medication():
    return {
        "name": "Medicine",
        "userId": VALID_USER_ID,
        "doseQuantity": 250.0,
        "doseUnits": "mg",
        "prn": True,
        "extraProperties": {},
    }


def history_item():
    return {
        **simple_medication(),
        "changeType": "MEDICATION_CREATE",
        "name": "Test Name",
    }


class BaseMedicationTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        MedicationComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/medication_dump.json"),
    ]

    def setUp(self):
        super().setUp()

        self.headers = self.get_headers_for_token("5e8f0c74b50aa9656c34789d")
        self.medication_route = (
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/medication/"
        )


class CreateMedicationTestCase(BaseMedicationTestCase):
    def test_create_medication_with_prn(self):
        response = self.flask_client.post(
            self.medication_route, json=simple_medication(), headers=self.headers
        )
        self.assertEqual(201, response.status_code)
        self.assertIsNotNone(response.json["id"])

    def test_failure_create_medication_wrong_payload_type(self):
        response = self.flask_client.post(
            self.medication_route, json=[], headers=self.headers
        )
        self.assertEqual(400, response.status_code)

    def test_create_medication_with_schedule(self):
        medication_dict = simple_medication()
        del medication_dict["prn"]
        medication_dict["schedule"] = {
            "frequency": 3,
            "period": 1,
            "periodUnit": "DAILY",
        }
        response = self.flask_client.post(
            self.medication_route, json=medication_dict, headers=self.headers
        )
        self.assertEqual(201, response.status_code)
        self.assertIsNotNone(response.json["id"])

    def test_create_medication_no_name(self):
        medication_dict = simple_medication()
        del medication_dict["name"]
        response = self.flask_client.post(
            self.medication_route, json=medication_dict, headers=self.headers
        )
        self.assertEqual(403, response.status_code)

    def test_create_medication_with_long_name(self):
        medication_dict = simple_medication()
        medication_dict["name"] = "PNEUMONOULTRAMICROSCOPICSILICOVOLCANOCONIOSIS"
        response = self.flask_client.post(
            self.medication_route, json=medication_dict, headers=self.headers
        )
        self.assertEqual(201, response.status_code)

    def test_create_medication_with_history(self):
        # should not update with the data that is passed to changeHistory
        medication_dict = simple_medication()
        medication_dict["changeHistory"] = [history_item()]
        rsp = self.flask_client.post(
            self.medication_route, json=medication_dict, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)

        options = {
            "skip": 0,
            "limit": 10,
            "startDateTime": "2020-05-04T10:00:00Z",
            "onlyEnabled": True,
        }
        response = self.flask_client.post(
            f"{self.medication_route}retrieve", json=options, headers=self.headers
        )
        self.assertEqual(200, response.status_code)
        for item in response.json:
            histories = item["changeHistory"]
            for history in histories:
                self.assertNotEqual(history["name"], history_item()["name"])

    def test_user_deployment_and_module_id_set_on_creation(self):
        # should not update with the data that is passed to changeHistory
        medication_dict = simple_medication()

        rsp = self.flask_client.post(
            self.medication_route, json=medication_dict, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        options = {
            "skip": 0,
            "limit": 10,
            "startDateTime": "2020-05-04T10:00:00Z",
            "onlyEnabled": True,
        }
        response = self.flask_client.post(
            f"{self.medication_route}retrieve", json=options, headers=self.headers
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))
        created_medication = response.json[1]
        self.assertEqual(
            created_medication[Medication.DEPLOYMENT_ID], USER_DEPLOYMENT_ID
        )
        self.assertEqual(
            created_medication[Medication.MODULE_ID], MedicationsModule.moduleId
        )


class RetrieveMedicationTestCase(BaseMedicationTestCase):
    def test_retrieve_medications(self):
        options = {
            "skip": 0,
            "limit": 10,
            "startDateTime": "2020-05-04T10:00:00Z",
            "onlyEnabled": True,
        }
        response = self.flask_client.post(
            f"{self.medication_route}retrieve", json=options, headers=self.headers
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json))
        self.assertEqual(1, len(response.json[-1]["changeHistory"]))

    def test_failure_retrieve_medication_wrong_payload_type(self):
        response = self.flask_client.post(
            f"{self.medication_route}retrieve", json=[], headers=self.headers
        )
        self.assertEqual(400, response.status_code)


class UpdateMedicationTestCase(BaseMedicationTestCase):
    def test_update_medication(self):
        response = self.flask_client.post(
            f"{self.medication_route}{VALID_MEDICATION_ID}",
            json=simple_medication(),
            headers=self.headers,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(VALID_MEDICATION_ID, response.json["id"])

    def test_failure_update_medication_wrong_payload_type(self):
        response = self.flask_client.post(
            f"{self.medication_route}{VALID_MEDICATION_ID}",
            json=[],
            headers=self.headers,
        )
        self.assertEqual(400, response.status_code)

    def test_medication_history(self):
        response = self.flask_client.post(
            f"{self.medication_route}{VALID_MEDICATION_ID}",
            json=simple_medication(),
            headers=self.headers,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(VALID_MEDICATION_ID, response.json["id"])

        options = {
            "skip": 0,
            "limit": 10,
            "startDateTime": "2020-05-04T10:00:00Z",
            "onlyEnabled": True,
        }
        response = self.flask_client.post(
            f"{self.medication_route}retrieve", json=options, headers=self.headers
        )
        self.assertEqual(200, response.status_code)

        med_history = response.json[-1]["changeHistory"]
        self.assertEqual(len(med_history), 2)

        for history in med_history:
            user_id = history.get("userId")
            self.assertEqual(type(user_id), str)

    def test_update_medication_with_medication_history(self):
        # should not update with the data that is passed to changeHistory
        medication_dict = simple_medication()
        del medication_dict["prn"]
        medication_dict["changeHistory"] = [history_item()]
        rsp = self.flask_client.post(
            f"{self.medication_route}{VALID_MEDICATION_ID}",
            json=medication_dict,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)

        options = {
            "skip": 0,
            "limit": 10,
            "startDateTime": "2020-05-04T10:00:00Z",
            "onlyEnabled": True,
        }
        response = self.flask_client.post(
            f"{self.medication_route}retrieve", json=options, headers=self.headers
        )
        self.assertEqual(200, response.status_code)

        for item in response.json:
            histories = item["changeHistory"]
            for history in histories:
                self.assertNotEqual(history["name"], history_item()["name"])

    def test_update_medication_invalid_id(self):
        response = self.flask_client.post(
            f"{self.medication_route}{INVALID_MEDICATION_ID}",
            json=simple_medication(),
            headers=self.headers,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual(400011, response.json["code"])

    def test_update_medication_invalid_user_id(self):
        response = self.flask_client.post(
            f"api/extensions/v1beta/user/{INVALID_USER_ID}/medication/{VALID_MEDICATION_ID}",
            json=simple_medication(),
            headers=self.headers,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual(UserErrorCodes.INVALID_USER_ID, response.json["code"])

    def test_delete_user_medication(self):
        def retrieve_user_medications():
            options = {
                "skip": 0,
                "limit": 10,
                "startDateTime": "2020-05-04T10:00:00Z",
                "onlyEnabled": True,
            }
            response = self.flask_client.post(
                f"{self.medication_route}retrieve", json=options, headers=self.headers
            )
            return response.json

        self.assertTrue(len(retrieve_user_medications()))

        super_admin_headers = self.get_headers_for_token(VALID_SUPER_ADMIN_ID)
        del_user_path = f"/api/extensions/v1beta/user/{VALID_USER_ID}/delete-user"
        rsp = self.flask_client.delete(del_user_path, headers=super_admin_headers)
        self.assertEqual(rsp.status_code, 204)

        rsp = retrieve_user_medications()
        self.assertEqual(UserErrorCodes.INVALID_USER_ID, rsp["code"])
