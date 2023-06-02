from extensions.kardia.router.kardia_requests import (
    RetrievePatientRecordingsRequestObject,
)
from extensions.kardia.use_case.base_kardia_use_case import BaseKardiaUseCase
from sdk.common.usecase.response_object import Response


class RetrievePatientRecordingsUseCase(BaseKardiaUseCase):
    def process_request(self, request_object: RetrievePatientRecordingsRequestObject):
        patient_recordings = (
            self._kardia_integration_client.retrieve_patient_recordings(
                request_object.patientId
            )
        )
        return Response(patient_recordings)
