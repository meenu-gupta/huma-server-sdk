from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.kardia.router.kardia_requests import (
    SyncKardiaDataRequestObject,
    RetrievePatientRecordingsRequestObject,
    RetrieveSingleEcgPdfRequestObject,
)
from extensions.kardia.use_case.retrieve_patient_recordings_use_case import (
    RetrievePatientRecordingsUseCase,
)
from extensions.kardia.use_case.retrieve_single_ecg_pdf_use_case import (
    RetrieveSingleEcgPdfUseCase,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class SyncKardiaDataUseCase(UseCase):
    @autoparams()
    def __init__(self, auth_repo: AuthorizationRepository):
        self._auth_repo = auth_repo

    @staticmethod
    def _retrieve_patient_recordings(kardia_id):
        req_recordings = RetrievePatientRecordingsRequestObject.from_dict(
            {RetrievePatientRecordingsRequestObject.PATIENT_ID: kardia_id}
        )
        patient_recordings = (
            RetrievePatientRecordingsUseCase().execute(req_recordings).value
        )
        return patient_recordings

    @staticmethod
    def _retrieve_single_ecg_pdf(recordings, user_id, deployment_id):
        primitives = []
        ecg_pdf_use_case = RetrieveSingleEcgPdfUseCase()
        for recording in recordings:
            req_ecg_pdf = RetrieveSingleEcgPdfRequestObject.from_dict(
                {
                    RetrieveSingleEcgPdfRequestObject.USER_ID: user_id,
                    RetrieveSingleEcgPdfRequestObject.RECORD_ID: recording.get("id"),
                    RetrieveSingleEcgPdfRequestObject.DEPLOYMENT_ID: deployment_id,
                }
            )

            primitives.append(ecg_pdf_use_case.execute(req_ecg_pdf).value)
        return primitives

    def process_request(self, request_object: SyncKardiaDataRequestObject):
        user = self._auth_repo.retrieve_simple_user_profile(
            user_id=request_object.userId
        )

        primitives = []

        if not user.kardiaId:
            return Response(primitives)

        patient_recordings = self._retrieve_patient_recordings(user.kardiaId)

        if not patient_recordings.get("recordings"):
            return Response(primitives)

        primitives = self._retrieve_single_ecg_pdf(
            patient_recordings.get("recordings"),
            request_object.userId,
            request_object.deploymentId,
        )

        return Response(primitives)
