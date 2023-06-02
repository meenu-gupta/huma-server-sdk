import datetime
import unittest
from unittest.mock import patch, MagicMock

from extensions.medication.repository.medication_repository import MedicationRepository
from extensions.medication.router.medication_request import (
    CreateMedicationRequestObject,
    RetrieveMedicationsRequestObject,
    UpdateMedicationRequestObject,
    DeleteMedicationRequestObject,
)
from extensions.medication.use_case.create_medication_use_case import (
    CreateMedicationUseCase,
)
from extensions.medication.use_case.retrieve_medications_use_case import (
    RetrieveMedicationsUseCase,
)
from extensions.medication.use_case.update_medication_use_case import (
    UpdateMedicationUseCase,
)
from extensions.medication.use_case.delete_medication_use_case import (
    DeleteMedicationUseCase,
)

from sdk.common.utils import inject

USE_CASE_PATH = "extensions.medication.use_case"
VALID_USER_ID = "5e84b0dab8dfa268b1180536"
VALID_MEDICATION_ID = "5eafd121b2d79d48ce4cd9e8"


def simple_medication():
    return {
        "name": "Medicine",
        "userId": VALID_USER_ID,
        "doseQuantity": 250.0,
        "doseUnits": "mg",
        "prn": True,
        "extraProperties": {},
    }


class MedicationUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._repo = MagicMock()

        def configure_binder(binder: inject.Binder):
            binder.bind(MedicationRepository, self._repo)

        inject.clear_and_configure(configure_binder)

    def test_success_create_medication_use_case(self):
        medication_dict = simple_medication()
        req_object = CreateMedicationRequestObject.from_dict(medication_dict)

        mocked_auth_repo = MagicMock()

        use_case = CreateMedicationUseCase(mocked_auth_repo)
        use_case.execute(req_object)

        self._repo.create_medication.assert_called_with(req_object)

    def test_success_retrieve_medication_use_case(self):
        dt = datetime.datetime(2012, 12, 24)
        req_object = RetrieveMedicationsRequestObject(
            userId="user_id", skip=1, limit=5, startDateTime=dt
        )

        mocked_medication_repo = MagicMock()

        use_case = RetrieveMedicationsUseCase(mocked_medication_repo)
        use_case.execute(req_object)

        mocked_medication_repo.retrieve_medications.assert_called_with(
            user_id=req_object.userId,
            skip=req_object.skip,
            limit=req_object.limit,
            start_date=req_object.startDateTime,
            only_enabled=True,
        )

    def test_success_update_medication_use_case(self):
        medication_dict = simple_medication()
        medication_dict.update({"id": VALID_MEDICATION_ID})

        req_object = UpdateMedicationRequestObject.from_dict(medication_dict)
        mocked_medication_repo = MagicMock()

        use_case = UpdateMedicationUseCase(mocked_medication_repo)
        use_case.execute(req_object)

        mocked_medication_repo.update_medication.assert_called_with(req_object)

    def test_success_delete_medication_use_case(self):
        session = MagicMock()
        req_object = DeleteMedicationRequestObject(
            userId=VALID_USER_ID, session=session
        )
        mocked_medication_repo = MagicMock()

        use_case = DeleteMedicationUseCase(mocked_medication_repo)
        use_case.execute(req_object)

        mocked_medication_repo.delete_user_medication.assert_called_with(
            user_id=req_object.userId, session=req_object.session
        )


if __name__ == "__main__":
    unittest.main()
