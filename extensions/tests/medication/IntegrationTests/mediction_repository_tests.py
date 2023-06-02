import unittest
from pathlib import Path

from bson import ObjectId

from extensions.exceptions import MedicationDoesNotExist
from extensions.medication.component import MedicationComponent
from extensions.medication.models.medication import Medication
from extensions.medication.repository.medication_repository import MedicationRepository
from extensions.medication.repository.mongo_medication_repository import (
    MongoMedicationRepository,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.common.utils.validators import utc_str_val_to_field

VALID_USER_ID = "5e84b0dab8dfa268b1180536"
INVALID_USER_ID = "6e84b0dab8dfa268b1180532"

VALID_MEDICATION_ID = "5eafd121b2d79d48ce4cd9e8"
INVALID_MEDICATION_ID = "2e8cc88d0e8f49bbe59d11ba"

MEDICATION_COLLECTION = "medication"


class MedicationMongoRepoTestCase(ExtensionTestCase):
    components = [MedicationComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/medication_dump.json")]

    @classmethod
    def setUpClass(cls) -> None:
        super(MedicationMongoRepoTestCase, cls).setUpClass()
        cls.repo: MedicationRepository = MongoMedicationRepository(
            database=cls.mongo_database
        )

    def test_retrieve_medication_by_id(self):
        medication = self.repo.retrieve_medication_by_id(
            medication_id=VALID_MEDICATION_ID
        )
        self.assertIsInstance(medication, Medication)
        self.assertEqual(medication.id, VALID_MEDICATION_ID)

    def test_create_medication_with_prn(self):
        medication_dict = {
            "name": "Medicine",
            "userId": VALID_USER_ID,
            "doseQuantity": 250.0,
            "doseUnits": "mg",
            "prn": True,
            "extraProperties": {},
        }
        created_id = self.repo.create_medication(Medication.from_dict(medication_dict))
        self.assertNotEqual(None, created_id)
        medication = self.repo.retrieve_medication_by_id(medication_id=created_id)
        medication = medication.to_dict(include_none=False)
        for key, value in medication_dict.items():
            self.assertEqual(
                value,
                str(medication[key])
                if isinstance(medication[key], ObjectId)
                else medication[key],
            )
        self.assertIsNotNone(medication["createDateTime"])
        self.assertEqual(medication["createDateTime"], medication["updateDateTime"])

    def test_create_medication_with_schedule(self):
        medication_dict = {
            "name": "Medicine",
            "userId": VALID_USER_ID,
            "doseQuantity": 250.0,
            "doseUnits": "mg",
            "schedule": {"frequency": 3, "period": 1, "periodUnit": "DAILY"},
            "extraProperties": {},
        }
        created_id = self.repo.create_medication(Medication.from_dict(medication_dict))
        self.assertNotEqual(None, created_id)
        medication = self.repo.retrieve_medication_by_id(medication_id=created_id)
        medication = medication.to_dict(include_none=False)
        for key, value in medication_dict.items():
            self.assertEqual(
                value,
                str(medication[key])
                if isinstance(medication[key], ObjectId)
                else medication[key],
            )
        self.assertIsNotNone(medication["createDateTime"])
        self.assertEqual(medication["createDateTime"], medication["updateDateTime"])

    def test_history_new_item_on_update_medication(self):
        medication_dict = {
            "id": VALID_MEDICATION_ID,
            "userId": VALID_USER_ID,
            "name": "Medicine Updated",
            "doseQuantity": 200.0,
            "doseUnits": "mg",
            "prn": True,
            "extraProperties": {},
            "enabled": True,
        }
        medication_before_update = self.repo.retrieve_medication_by_id(
            medication_id=VALID_MEDICATION_ID
        )
        self.assertEqual(len(medication_before_update.changeHistory), 1)

        updated_id = self.repo.update_medication(Medication.from_dict(medication_dict))
        self.assertEqual(medication_dict["id"], updated_id)
        medication = self.repo.retrieve_medication_by_id(medication_id=updated_id)
        medication = medication.to_dict(include_none=False)
        self.assertEqual(len(medication["changeHistory"]), 2)
        self.assertEqual(medication["changeHistory"][0]["name"], "Medicine")
        self.assertEqual(medication["changeHistory"][0]["doseQuantity"], 250.0)
        self.assertEqual(medication["changeHistory"][-1]["name"], "Medicine Updated")
        self.assertEqual(medication["changeHistory"][-1]["doseQuantity"], 200.0)
        self.assertEqual(
            medication["changeHistory"][-1]["changeType"], "MEDICATION_UPDATE"
        )

    def test_history_on_delete_medication(self):
        medication_dict = {
            "id": VALID_MEDICATION_ID,
            "userId": VALID_USER_ID,
            "name": "Medicine Updated",
            "doseQuantity": 200.0,
            "doseUnits": "mg",
            "prn": True,
            "extraProperties": {},
            "enabled": False,
        }

        updated_id = self.repo.update_medication(Medication.from_dict(medication_dict))
        self.assertEqual(medication_dict["id"], updated_id)
        medication = self.repo.retrieve_medication_by_id(medication_id=updated_id)
        medication = medication.to_dict(include_none=False)
        self.assertEqual(len(medication["changeHistory"]), 2)
        self.assertEqual(
            medication["changeHistory"][-1]["changeType"], "MEDICATION_DELETE"
        )

    def test_history_on_create_medication(self):
        medication_dict = {
            "name": "Medicine",
            "userId": VALID_USER_ID,
            "doseQuantity": 250.0,
            "doseUnits": "mg",
            "prn": True,
            "extraProperties": {},
        }
        created_id = self.repo.create_medication(Medication.from_dict(medication_dict))
        self.assertNotEqual(None, created_id)
        medication = self.repo.retrieve_medication_by_id(medication_id=created_id)
        medication = medication.to_dict(include_none=False)
        self.assertEqual(
            medication["changeHistory"][-1]["changeType"], "MEDICATION_CREATE"
        )

    def test_update_medication(self):
        medication_dict = {
            "id": VALID_MEDICATION_ID,
            "userId": VALID_USER_ID,
            "name": "Medicine Updated",
            "doseQuantity": 200.0,
            "doseUnits": "mg",
            "prn": True,
            "extraProperties": {},
        }
        updated_id = self.repo.update_medication(Medication.from_dict(medication_dict))
        self.assertEqual(medication_dict["id"], updated_id)
        medication = self.repo.retrieve_medication_by_id(medication_id=updated_id)
        medication = medication.to_dict(include_none=False)
        self.assertIsNotNone(medication["updateDateTime"])
        self.assertGreater(medication["updateDateTime"], medication["createDateTime"])

    def test_update_medication_invalid_id(self):
        medication_dict = {
            "id": INVALID_MEDICATION_ID,
            "userId": VALID_USER_ID,
            "name": "Medicine Updated",
            "doseQuantity": 200.0,
            "doseUnits": "mg",
            "prn": True,
            "extraProperties": {},
        }
        with self.assertRaises(MedicationDoesNotExist):
            self.repo.update_medication(Medication.from_dict(medication_dict))

    def test_retrieve_medications(self):
        date = utc_str_val_to_field("2020-05-04T10:00:00Z")
        medications = self.repo.retrieve_medications(
            user_id=VALID_USER_ID, skip=0, limit=10, start_date=date
        )
        self.assertEqual(1, len(medications))

    def test_retrieve_medications_invalid_user_id(self):
        date = utc_str_val_to_field("2020-05-04T10:00:00Z")
        medications = self.repo.retrieve_medications(
            user_id=INVALID_MEDICATION_ID, skip=0, limit=10, start_date=date
        )
        self.assertEqual(0, len(medications))

    def test_retrieve_medications_invalid_date(self):
        date = utc_str_val_to_field("2021-05-04T10:00:00Z")
        medications = self.repo.retrieve_medications(
            user_id=INVALID_MEDICATION_ID, skip=0, limit=10, start_date=date
        )
        self.assertEqual(0, len(medications))


if __name__ == "__main__":
    unittest.main()
