import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

from extensions.authorization.models.user import User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.kardia.repository.kardia_integration_client import (
    KardiaIntegrationClient,
)
from extensions.kardia.router.kardia_requests import (
    CreateKardiaPatientRequestObject,
    RetrievePatientRecordingsRequestObject,
    RetrieveSingleEcgRequestObject,
    RetrieveSingleEcgPdfRequestObject,
    SyncKardiaDataRequestObject,
)
from extensions.kardia.use_case.create_kardia_patient_use_case import (
    CreateKardiaPatientUseCase,
)
from extensions.kardia.use_case.retrieve_patient_recordings_use_case import (
    RetrievePatientRecordingsUseCase,
)
from extensions.kardia.use_case.retrieve_single_ecg_pdf_use_case import (
    RetrieveSingleEcgPdfUseCase,
)
from extensions.kardia.use_case.retrieve_single_ecg_use_case import (
    RetrieveSingleEcgUseCase,
)
from extensions.kardia.use_case.sync_kardia_data_use_case import SyncKardiaDataUseCase
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig


KARDIA_USE_CASE_PATH = "extensions.kardia.use_case"
KARDIA_INJECT_PATH = f"{KARDIA_USE_CASE_PATH}.base_kardia_use_case.inject"
KARDIA_CREATE_PATIENT_PATH = f"{KARDIA_USE_CASE_PATH}.create_kardia_patient_use_case"
SAMPLE_ID = "600a8476a961574fb38157d5"
SAMPLE_USER = User.from_dict({User.ID: SAMPLE_ID})
RECORD_ID = "600a8476a961574fb3815aaa"

testapp = Flask(__name__)
testapp.app_context().push()


class MockInject:
    instance = MagicMock()


class MockAuthRepo:
    update_user_profile = MagicMock()
    retrieve_simple_user_profile = MagicMock()
    retrieve_simple_user_profile.return_value = User.from_dict(
        {User.KARDIA_ID: SAMPLE_ID}
    )


class MockModuleResultRepo:
    retrieve_primitives = MagicMock(return_value=None)
    create_primitive = MagicMock()


class MockKardiaClient:
    create_kardia_patient = MagicMock(return_value={"id": "some id"})
    retrieve_single_ecg_pdf = MagicMock(return_value="some content")
    retrieve_patient_recordings = MagicMock()
    retrieve_single_ecg = MagicMock()


class MockServerConfig:
    server = MagicMock()
    server.storage.defaultBucket = "bucket"


class KardiaUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._kardia_client = MockKardiaClient()
        self._auth_repo = MockAuthRepo()
        self._module_result_repo = MockModuleResultRepo()
        self._server_config = MockServerConfig()

        def configure_with_binder(binder: inject.Binder):
            binder.bind(KardiaIntegrationClient, self._kardia_client)
            binder.bind(AuthorizationRepository, self._auth_repo)
            binder.bind(ModuleResultRepository, self._module_result_repo)
            binder.bind(PhoenixServerConfig, self._server_config)

        inject.clear_and_configure(config=configure_with_binder)

    @patch(f"{KARDIA_CREATE_PATIENT_PATH}.UpdateUserProfileRequestObject")
    def test_success_create_kardia_patient(self, mock_req):
        email = "user@huma.com"
        dob = "10/10/2010"
        req = CreateKardiaPatientRequestObject.from_dict(
            {
                CreateKardiaPatientRequestObject.DOB: dob,
                CreateKardiaPatientRequestObject.EMAIL: email,
                CreateKardiaPatientRequestObject.USER: SAMPLE_USER,
            }
        )
        CreateKardiaPatientUseCase().execute(req)
        mock_req.from_dict.assert_called_with(
            {
                mock_req.ID: SAMPLE_ID,
                mock_req.KARDIA_ID: self._kardia_client.create_kardia_patient().get(
                    "id"
                ),
                mock_req.PREVIOUS_STATE: SAMPLE_USER,
            }
        )
        self._auth_repo.update_user_profile.assert_called_once()

    def test_success_retrieve_patient_recordings(self):
        request_object = RetrievePatientRecordingsRequestObject.from_dict(
            {RetrievePatientRecordingsRequestObject.PATIENT_ID: SAMPLE_ID}
        )
        RetrievePatientRecordingsUseCase().execute(request_object)
        self._kardia_client.retrieve_patient_recordings.assert_called_with(SAMPLE_ID)

    def test_success_retrieve_single_ecg(self):
        request_object = RetrieveSingleEcgRequestObject.from_dict(
            {RetrieveSingleEcgRequestObject.RECORD_ID: SAMPLE_ID}
        )
        RetrieveSingleEcgUseCase().execute(request_object)
        self._kardia_client.retrieve_single_ecg.assert_called_with(SAMPLE_ID)

    @patch(f"{KARDIA_USE_CASE_PATH}.retrieve_single_ecg_pdf_use_case.ECGAliveCor")
    @patch(f"{KARDIA_USE_CASE_PATH}.retrieve_single_ecg_pdf_use_case.UploadFileUseCase")
    @patch(
        f"{KARDIA_USE_CASE_PATH}.retrieve_single_ecg_pdf_use_case.UploadFileRequestObject"
    )
    def test_success_retrieve_single_ecg_pdf(self, mock_req, mock_use_case, mock_ecg):
        request_object = RetrieveSingleEcgPdfRequestObject.from_dict(
            {
                RetrieveSingleEcgPdfRequestObject.USER_ID: SAMPLE_ID,
                RetrieveSingleEcgPdfRequestObject.RECORD_ID: RECORD_ID,
                RetrieveSingleEcgPdfRequestObject.DEPLOYMENT_ID: SAMPLE_ID,
            }
        )
        mock_ecg.__name__ = "ecg"
        mock_ecg.KARDIA_ECG_RECORD_ID = RECORD_ID
        mock_ecg.from_dict = MagicMock()
        RetrieveSingleEcgPdfUseCase().execute(request_object)
        self._kardia_client.retrieve_single_ecg_pdf.assert_called_with(RECORD_ID)
        mock_req.from_dict.assert_called_with(
            {
                mock_req.BUCKET: self._server_config.server.storage.defaultBucket,
                mock_req.FILENAME: f"user/{SAMPLE_ID}/ECGAliveCor/{RECORD_ID}.pdf",
                mock_req.FILE_DATA: self._kardia_client.retrieve_single_ecg_pdf(),
            }
        )
        self._module_result_repo.retrieve_primitives.assert_called_once()
        mock_use_case().execute.assert_called_once()
        self._module_result_repo.create_primitive.assert_called_once()

    @patch(
        f"{KARDIA_USE_CASE_PATH}.sync_kardia_data_use_case.RetrievePatientRecordingsUseCase"
    )
    @patch(
        f"{KARDIA_USE_CASE_PATH}.sync_kardia_data_use_case.RetrieveSingleEcgPdfUseCase"
    )
    def test_success_sync_kardia_data(self, mock_ecg_use_case, mock_recording_use_case):
        request_object = SyncKardiaDataRequestObject.from_dict(
            {
                SyncKardiaDataRequestObject.USER_ID: SAMPLE_ID,
                SyncKardiaDataRequestObject.DEPLOYMENT_ID: SAMPLE_ID,
            }
        )
        mock_recording_use_case().execute().value = {
            "recordings": [{"id": SAMPLE_ID}, {"id": SAMPLE_ID}]
        }
        mock_ecg_use_case().excute.value = MagicMock()
        res = SyncKardiaDataUseCase().execute(request_object)
        self._auth_repo.retrieve_simple_user_profile.assert_called_once()
        self.assertEqual(len(res.value), 2)


if __name__ == "__main__":
    unittest.main()
