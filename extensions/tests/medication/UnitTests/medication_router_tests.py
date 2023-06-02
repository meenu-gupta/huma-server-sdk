import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.medication.models.medication import Medication
from extensions.medication.router.medication_router import (
    update_medication,
    retrieve_medications,
    create_medication,
)
from sdk.phoenix.audit_logger import AuditLog

MEDICATION_ROUTER_PATH = "extensions.medication.router.medication_router"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{MEDICATION_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch.object(AuditLog, "create_log", MagicMock())
class MedicationRouterTestCase(unittest.TestCase):
    @patch(f"{MEDICATION_ROUTER_PATH}.jsonify")
    @patch(f"{MEDICATION_ROUTER_PATH}.UpdateMedicationRequestObject")
    @patch(f"{MEDICATION_ROUTER_PATH}.UpdateMedicationUseCase")
    def test_success_update_medication(self, use_case, req_obj, jsonify):
        user_id = SAMPLE_ID
        medication_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            update_medication(user_id, medication_id)
            req_obj.from_dict.assert_called_with(
                {**payload, Medication.USER_ID: user_id, Medication.ID: medication_id}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{MEDICATION_ROUTER_PATH}.jsonify")
    @patch(f"{MEDICATION_ROUTER_PATH}.RetrieveMedicationsRequestObject")
    @patch(f"{MEDICATION_ROUTER_PATH}.RetrieveMedicationsUseCase")
    def test_success_retrieve_medications(self, use_case, req_obj, jsonify):
        user_id = SAMPLE_ID
        payload = {
            "skip": 0,
            "limit": 10,
            "startDateTime": "2020-05-04T10:00:00Z",
            "onlyEnabled": True,
        }
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            retrieve_medications(user_id)
            req_obj.from_dict.assert_called_with({**payload, req_obj.USER_ID: user_id})
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().medication_to_dict())

    @patch(f"{MEDICATION_ROUTER_PATH}.jsonify")
    @patch(f"{MEDICATION_ROUTER_PATH}.CreateMedicationRequestObject")
    @patch(f"{MEDICATION_ROUTER_PATH}.CreateMedicationUseCase")
    def test_success_create_medication(self, use_case, req_obj, jsonify):
        user_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_medication(user_id)
            req_obj.from_dict.assert_called_with(
                {**payload, Medication.USER_ID: user_id}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})


if __name__ == "__main__":
    unittest.main()
