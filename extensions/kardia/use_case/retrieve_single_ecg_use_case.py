from extensions.kardia.router.kardia_requests import RetrieveSingleEcgRequestObject
from extensions.kardia.use_case.base_kardia_use_case import BaseKardiaUseCase
from sdk.common.usecase.response_object import Response


class RetrieveSingleEcgUseCase(BaseKardiaUseCase):
    def process_request(self, request_object: RetrieveSingleEcgRequestObject):
        single_ecg = self._kardia_integration_client.retrieve_single_ecg(
            request_object.recordId
        )
        return Response(single_ecg)
