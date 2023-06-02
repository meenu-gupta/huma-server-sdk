from extensions.medication.use_case.base_medication_use_case import (
    BaseMedicationUseCase,
)
from extensions.medication.router.medication_request import (
    RetrieveMedicationsRequestObject,
)
from extensions.medication.router.medication_response import MedicationResponse


class RetrieveMedicationsUseCase(BaseMedicationUseCase):
    def process_request(self, request_object: RetrieveMedicationsRequestObject):
        medication_list = self._repo.retrieve_medications(
            user_id=request_object.userId,
            skip=request_object.skip,
            limit=request_object.limit,
            start_date=request_object.startDateTime,
            only_enabled=request_object.onlyEnabled,
        )

        return MedicationResponse(value=medication_list)
