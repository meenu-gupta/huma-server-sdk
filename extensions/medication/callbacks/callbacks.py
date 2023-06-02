from sdk.auth.events.delete_user_event import DeleteUserEvent
from extensions.common.monitoring import report_exception
from extensions.medication.router.medication_request import (
    DeleteMedicationRequestObject,
)
from extensions.medication.use_case.delete_medication_use_case import (
    DeleteMedicationUseCase,
)


def on_user_delete_callback(event: DeleteUserEvent):
    req_object = DeleteMedicationRequestObject(
        userId=event.user_id, session=event.session
    )
    try:
        DeleteMedicationUseCase().execute(req_object)
    except Exception as error:
        report_exception(
            error,
            context_name="DeleteUserMedication",
            context_content={"userId": event.user_id},
        )
        raise error
