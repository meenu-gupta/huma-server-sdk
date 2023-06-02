import copy
import unittest

from extensions.medication.models.medication import Medication, MedicationHistory
from extensions.medication.router.medication_request import (
    CreateMedicationRequestObject,
    UpdateMedicationRequestObject,
    RetrieveMedicationsRequestObject,
    DeleteMedicationRequestObject,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_VALID_OBJ_ID = "60a20766c85cd55b38c99e12"


class CreateMedicationRequestObjectTestCase(unittest.TestCase):
    def test_success_create_medication_request_object(self):
        try:
            CreateMedicationRequestObject.from_dict(
                {
                    Medication.USER_ID: SAMPLE_VALID_OBJ_ID,
                    Medication.NAME: "test medication name",
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_creation_no_required_fields(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CreateMedicationRequestObject.from_dict(
                {
                    Medication.USER_ID: SAMPLE_VALID_OBJ_ID,
                }
            )

        with self.assertRaises(ConvertibleClassValidationError):
            CreateMedicationRequestObject.from_dict(
                {Medication.NAME: "test medication name"}
            )

    def test_failure_must_not_be_present_fields(self):
        must_not_be_present_fields = {
            Medication.ID: SAMPLE_VALID_OBJ_ID,
            Medication.CREATE_DATE_TIME: "2020-01-01T00:00:00Z",
            Medication.UPDATE_DATE_TIME: "2020-01-01T00:00:00Z",
            Medication.CHANGE_HISTORY: [
                MedicationHistory(
                    changeType=MedicationHistory.ChangeType.MEDICATION_CREATE
                )
            ],
        }
        sample_data = {
            Medication.USER_ID: SAMPLE_VALID_OBJ_ID,
            Medication.NAME: "test medication name",
        }
        for field in must_not_be_present_fields:
            data = copy.deepcopy(sample_data)
            data[field] = must_not_be_present_fields[field]
            with self.assertRaises(ConvertibleClassValidationError):
                CreateMedicationRequestObject.from_dict(data)


class UpdateMedicationRequestObjectTestCase(unittest.TestCase):
    def test_success_update_medication_req_obj(self):
        try:
            UpdateMedicationRequestObject.from_dict(
                {
                    Medication.ID: SAMPLE_VALID_OBJ_ID,
                    Medication.USER_ID: SAMPLE_VALID_OBJ_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_must_not_be_present(self):
        with self.assertRaises(ConvertibleClassValidationError):
            UpdateMedicationRequestObject.from_dict(
                {
                    Medication.ID: SAMPLE_VALID_OBJ_ID,
                    Medication.USER_ID: SAMPLE_VALID_OBJ_ID,
                    Medication.CHANGE_HISTORY: [
                        MedicationHistory(
                            changeType=MedicationHistory.ChangeType.MEDICATION_CREATE
                        )
                    ],
                }
            )


class RetrieveMedicationRequestObjectTestCase(unittest.TestCase):
    def test_success_retrieve_medication(self):
        try:
            RetrieveMedicationsRequestObject.from_dict(
                {
                    RetrieveMedicationsRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID,
                    RetrieveMedicationsRequestObject.SKIP: 5,
                    RetrieveMedicationsRequestObject.LIMIT: 10,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_no_required_fields(self):
        sample_dict = {
            RetrieveMedicationsRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID,
            RetrieveMedicationsRequestObject.SKIP: 5,
            RetrieveMedicationsRequestObject.LIMIT: 10,
        }
        for field in sample_dict:
            data = copy.deepcopy(sample_dict)
            data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                RetrieveMedicationsRequestObject.from_dict(data)


class DeleteMedicationRequestObjectTestCase(unittest.TestCase):
    def test_success_delete_user_medication(self):
        try:
            DeleteMedicationRequestObject.from_dict(
                {DeleteMedicationRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID}
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_no_required_fields(self):
        sample_dict = {DeleteMedicationRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID}
        data = copy.copy(sample_dict)
        data.pop(DeleteMedicationRequestObject.USER_ID)
        with self.assertRaises(ConvertibleClassValidationError):
            DeleteMedicationRequestObject.from_dict(data)


if __name__ == "__main__":
    unittest.main()
