import unittest
from unittest.mock import MagicMock

from bson import ObjectId
from freezegun import freeze_time
from freezegun.api import FakeDatetime

from extensions.medication.models.medication import Medication, MedicationHistory
from extensions.medication.repository.mongo_medication_repository import (
    MongoMedicationRepository,
)
from sdk.common.utils.validators import remove_none_values

SAMPLE_ID = "600a8476a961574fb38157d5"
MEDICATION_COLLECTION = MongoMedicationRepository.MEDICATION_COLLECTION


class MedicationRepoTestCase(unittest.TestCase):
    def test_success_delete_medication_on_user_delete(self):
        db = MagicMock()
        session = MagicMock()
        repo = MongoMedicationRepository(db)
        repo.delete_user_medication(user_id=SAMPLE_ID, session=session)
        user_id = ObjectId(SAMPLE_ID)
        db[repo.MEDICATION_COLLECTION].delete_many.assert_called_with(
            {Medication.USER_ID: user_id}, session=session
        )

    @freeze_time("2012-01-01")
    def test_success_create_medication(self):
        db = MagicMock()
        repo = MongoMedicationRepository(db)
        medication = Medication.from_dict({Medication.USER_ID: SAMPLE_ID})
        repo.create_medication(medication)
        query = {
            Medication.USER_ID: ObjectId(SAMPLE_ID),
            Medication.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
            Medication.CREATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
            Medication.CHANGE_HISTORY: [
                {
                    MedicationHistory.USER_ID: ObjectId(SAMPLE_ID),
                    MedicationHistory.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                    MedicationHistory.CREATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                    MedicationHistory.CHANGE_TYPE: MedicationHistory.ChangeType.MEDICATION_CREATE.name,
                }
            ],
        }
        db[MEDICATION_COLLECTION].insert_one.assert_called_with(query)

    def test_success_retrieve_medication(self):
        db = MagicMock()
        repo = MongoMedicationRepository(db)
        skip = 5
        limit = 10
        user_id = SAMPLE_ID
        start_date = FakeDatetime(2012, 1, 1, 0, 0)
        repo.retrieve_medications(
            skip=skip, limit=limit, user_id=user_id, start_date=start_date
        )
        query = {
            Medication.USER_ID: ObjectId(SAMPLE_ID),
            Medication.UPDATE_DATE_TIME: {"$gte": FakeDatetime(2012, 1, 1, 0, 0)},
            Medication.ENABLED: True,
        }
        db[MEDICATION_COLLECTION].find.assert_called_with(query)

    def test_success_retrieve_medication_by_id(self):
        db = MagicMock()
        repo = MongoMedicationRepository(db)
        medication_id = SAMPLE_ID
        db[MEDICATION_COLLECTION].find_one.return_value = {
            Medication.USER_ID: ObjectId(SAMPLE_ID),
            Medication.ID_: ObjectId(SAMPLE_ID),
            Medication.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
            Medication.CREATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
            Medication.CHANGE_HISTORY: [
                {
                    MedicationHistory.USER_ID: ObjectId(SAMPLE_ID),
                    MedicationHistory.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                    MedicationHistory.CREATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                    MedicationHistory.CHANGE_TYPE: MedicationHistory.ChangeType.MEDICATION_CREATE.name,
                }
            ],
        }
        repo.retrieve_medication_by_id(medication_id=medication_id)
        db[MEDICATION_COLLECTION].find_one.assert_called_with(
            {Medication.ID_: ObjectId(medication_id)}
        )

    @freeze_time("2012-01-01")
    def test_success_update_medication(self):
        db = MagicMock()
        repo = MongoMedicationRepository(db)
        medication_dict = {
            Medication.ID: ObjectId(SAMPLE_ID),
            Medication.USER_ID: ObjectId(SAMPLE_ID),
            Medication.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
            Medication.CREATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
        }
        medication = Medication.from_dict(medication_dict)
        medication_dict.pop(Medication.ID)
        repo.update_medication(medication)
        upd_query = {
            "$set": remove_none_values(medication_dict),
            "$push": {
                Medication.CHANGE_HISTORY: {
                    **medication_dict,
                    "changeType": MongoMedicationRepository._set_change_type(
                        medication_dict
                    ),
                }
            },
        }
        db[MEDICATION_COLLECTION].update_one.assert_called_with(
            {
                Medication.ID_: ObjectId(SAMPLE_ID),
                Medication.USER_ID: ObjectId(SAMPLE_ID),
            },
            upd_query,
        )


if __name__ == "__main__":
    unittest.main()
