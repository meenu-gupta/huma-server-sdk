import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.authorization.models.user import User
from extensions.kardia.router.kardia_requests import CreateKardiaPatientRequestObject
from extensions.kardia.router.kardia_router import (
    sync_kardia_data,
    retrieve_single_ecg_pdf,
    retrieve_single_ecg,
    retrieve_patient_recordings,
    create_kardia_patient,
)
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.audit_logger import AuditLog

KARDIA_ROUTER_PATH = "extensions.kardia.router.kardia_router"
SAMPLE_ID = "600a8476a961574fb38157d5"
SAMPLE_USER = User.from_dict({User.ID: SAMPLE_ID})

testapp = Flask(__name__)
testapp.app_context().push()


class MockG:
    user = SAMPLE_USER
    authz_user = MagicMock()
    authz_user.deployment_id = MagicMock(return_value=SAMPLE_ID)


@patch(
    f"{KARDIA_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch.object(AuditLog, "create_log", MagicMock())
class KardiaRouterTestCase(unittest.TestCase):
    @patch(f"{KARDIA_ROUTER_PATH}.g", MockG)
    @patch(f"{KARDIA_ROUTER_PATH}.jsonify")
    @patch(f"{KARDIA_ROUTER_PATH}.SyncKardiaDataUseCase")
    @patch(f"{KARDIA_ROUTER_PATH}.SyncKardiaDataRequestObject")
    def test_success_sync_kardia_data(self, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            sync_kardia_data(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.USER_ID: user_id,
                    req_obj.DEPLOYMENT_ID: MockG().authz_user.deployment_id(),
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{KARDIA_ROUTER_PATH}.g", MockG)
    @patch(f"{KARDIA_ROUTER_PATH}.jsonify")
    @patch(f"{KARDIA_ROUTER_PATH}.RetrieveSingleEcgPdfUseCase")
    @patch(f"{KARDIA_ROUTER_PATH}.RetrieveSingleEcgPdfRequestObject")
    def test_success_retrieve_single_ecg_pdf(self, req_obj, use_case, jsonify):
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_single_ecg_pdf(SAMPLE_ID, SAMPLE_ID)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.USER_ID: SAMPLE_ID,
                    req_obj.RECORD_ID: SAMPLE_ID,
                    req_obj.DEPLOYMENT_ID: MockG().authz_user.deployment_id(),
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{KARDIA_ROUTER_PATH}.jsonify")
    @patch(f"{KARDIA_ROUTER_PATH}.RetrieveSingleEcgUseCase")
    @patch(f"{KARDIA_ROUTER_PATH}.RetrieveSingleEcgRequestObject")
    def test_success_retrieve_single_ecg(self, req_obj, use_case, jsonify):
        record_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_single_ecg(record_id)
            req_obj.from_dict.assert_called_with({req_obj.RECORD_ID: record_id})
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{KARDIA_ROUTER_PATH}.jsonify")
    @patch(f"{KARDIA_ROUTER_PATH}.RetrievePatientRecordingsUseCase")
    @patch(f"{KARDIA_ROUTER_PATH}.RetrievePatientRecordingsRequestObject")
    def test_success_retrieve_patient_recordings(self, req_obj, use_case, jsonify):
        patient_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_patient_recordings(patient_id)
            req_obj.from_dict.assert_called_with({req_obj.PATIENT_ID: patient_id})
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{KARDIA_ROUTER_PATH}.g")
    @patch(f"{KARDIA_ROUTER_PATH}.jsonify")
    @patch(f"{KARDIA_ROUTER_PATH}.CreateKardiaPatientUseCase")
    @patch(f"{KARDIA_ROUTER_PATH}.CreateKardiaPatientRequestObject")
    def test_success_create_kardia_patient(self, req_obj, use_case, jsonify, mock_g):
        user_id = SAMPLE_ID
        payload = {
            CreateKardiaPatientRequestObject.EMAIL: "user@huma.com",
            CreateKardiaPatientRequestObject.DOB: "10/10/2010",
        }
        mock_g.user = MagicMock()
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_kardia_patient(user_id)
            req_obj.from_dict.assert_called_with({**payload, req_obj.USER: mock_g.user})
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)


if __name__ == "__main__":
    unittest.main()
