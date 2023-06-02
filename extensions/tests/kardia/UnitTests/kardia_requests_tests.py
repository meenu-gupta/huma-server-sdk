import unittest

from extensions.authorization.models.user import User
from extensions.kardia.router.kardia_requests import (
    CreateKardiaPatientRequestObject,
    RetrievePatientRecordingsRequestObject,
    RetrieveSingleEcgRequestObject,
    RetrieveSingleEcgPdfRequestObject,
    SyncKardiaDataRequestObject,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError


SAMPLE_VALID_OBJ_ID = "60a20766c85cd55b38c99e12"
SAMPLE_USER = User.from_dict({})


class CreateKardiaPatientRequestObjectTestCase(unittest.TestCase):
    def test_success_create_kardia_patient_req_obj(self):
        try:
            CreateKardiaPatientRequestObject.from_dict(
                {
                    CreateKardiaPatientRequestObject.EMAIL: "some_email@mail.com",
                    CreateKardiaPatientRequestObject.DOB: "2020-01-01",
                    CreateKardiaPatientRequestObject.USER: SAMPLE_USER,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_missed_required_fields(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CreateKardiaPatientRequestObject.from_dict(
                {
                    CreateKardiaPatientRequestObject.EMAIL: "some_email@mail.com",
                }
            )

        with self.assertRaises(ConvertibleClassValidationError):
            CreateKardiaPatientRequestObject.from_dict(
                {CreateKardiaPatientRequestObject.DOB: "2020-01-01"}
            )


class RetrievePatientRecordingsRequestObjectTestCase(unittest.TestCase):
    def test_success_retrieve_patient_req_obj(self):
        try:
            RetrievePatientRecordingsRequestObject.from_dict(
                {
                    RetrievePatientRecordingsRequestObject.PATIENT_ID: SAMPLE_VALID_OBJ_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_missed_required_fields(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrievePatientRecordingsRequestObject.from_dict({})


class RetrieveSingleEcgRequestObjectTestCase(unittest.TestCase):
    def test_success_retrieve_ecg_req_obj(self):
        try:
            RetrieveSingleEcgRequestObject.from_dict(
                {
                    RetrieveSingleEcgRequestObject.RECORD_ID: SAMPLE_VALID_OBJ_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_missed_required_fields(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveSingleEcgRequestObject.from_dict({})


class RetrieveSingleEcgPdfRequestObjectTestCase(unittest.TestCase):
    def test_success_retrieve_ecg_pdf_req_obj(self):
        try:
            RetrieveSingleEcgPdfRequestObject.from_dict(
                {
                    RetrieveSingleEcgPdfRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID,
                    RetrieveSingleEcgPdfRequestObject.RECORD_ID: SAMPLE_VALID_OBJ_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_missed_required_fields(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveSingleEcgPdfRequestObject.from_dict(
                {
                    RetrieveSingleEcgPdfRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID,
                }
            )

        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveSingleEcgPdfRequestObject.from_dict(
                {RetrieveSingleEcgPdfRequestObject.RECORD_ID: SAMPLE_VALID_OBJ_ID}
            )


class SyncKardiaDataRequestObjectTestCase(unittest.TestCase):
    def test_success_sync_kardia_req_obj(self):
        try:
            SyncKardiaDataRequestObject.from_dict(
                {
                    SyncKardiaDataRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_missed_required_fields(self):
        with self.assertRaises(ConvertibleClassValidationError):
            SyncKardiaDataRequestObject.from_dict({})


if __name__ == "__main__":
    unittest.main()
