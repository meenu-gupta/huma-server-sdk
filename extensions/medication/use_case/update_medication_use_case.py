from extensions.medication.use_case.base_medication_use_case import (
    BaseMedicationUseCase,
)
from extensions.medication.router.medication_request import (
    UpdateMedicationRequestObject,
)
from sdk.common.usecase.response_object import Response


class UpdateMedicationUseCase(BaseMedicationUseCase):
    def process_request(self, request_object: UpdateMedicationRequestObject):
        medication_id = self._repo.update_medication(request_object)

        return Response(medication_id)
