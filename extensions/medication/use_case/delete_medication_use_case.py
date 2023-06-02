from extensions.medication.use_case.base_medication_use_case import (
    BaseMedicationUseCase,
)
from extensions.medication.router.medication_request import (
    DeleteMedicationRequestObject,
)
from sdk.common.usecase.response_object import Response


class DeleteMedicationUseCase(BaseMedicationUseCase):
    def process_request(self, request_object: DeleteMedicationRequestObject):
        medication_id = self._repo.delete_user_medication(
            user_id=request_object.userId, session=request_object.session
        )

        return Response(medication_id)
