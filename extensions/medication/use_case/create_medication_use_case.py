from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.medication.router.medication_request import (
    CreateMedicationRequestObject,
)
from extensions.medication.use_case.base_medication_use_case import (
    BaseMedicationUseCase,
)
from sdk.common.usecase.response_object import Response
from sdk.common.utils.inject import autoparams


class CreateMedicationUseCase(BaseMedicationUseCase):
    @autoparams()
    def __init__(self, auth_repo: AuthorizationRepository):
        super(CreateMedicationUseCase, self).__init__()
        self._auth_repo = auth_repo

    def process_request(self, request_object: CreateMedicationRequestObject):
        medication_id = self._repo.create_medication(request_object)

        return Response(medication_id)
