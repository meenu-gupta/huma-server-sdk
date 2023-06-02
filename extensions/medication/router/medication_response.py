from extensions.medication.models.medication import Medication
from sdk.common.usecase.response_object import Response


class MedicationResponse(Response):
    @staticmethod
    def medication_to_dict(medications: list[Medication]) -> list[dict]:
        return [
            medication.to_dict(
                include_none=False,
                ignored_fields=[medication.USER_ID, medication.DEPLOYMENT_ID],
            )
            for medication in medications
        ]
