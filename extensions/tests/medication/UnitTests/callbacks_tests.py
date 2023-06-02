import unittest
from unittest.mock import MagicMock, patch

from extensions.medication.callbacks.callbacks import on_user_delete_callback
from sdk.auth.events.delete_user_event import DeleteUserEvent

CALLBACK_PATH = "extensions.medication.callbacks.callbacks"
SAMPLE_VALID_OBJ_ID = "60a20766c85cd55b38c99e12"


class CallbacksTestCase(unittest.TestCase):
    @patch(f"{CALLBACK_PATH}.DeleteMedicationUseCase")
    @patch(f"{CALLBACK_PATH}.DeleteMedicationRequestObject")
    def test_success_on_user_delete_callback(
        self, delete_medication_request_object, delete_medication_use_case
    ):
        session = MagicMock()
        event = DeleteUserEvent(session=session, user_id=SAMPLE_VALID_OBJ_ID)
        on_user_delete_callback(event)
        delete_medication_request_object.assert_called_with(
            session=session, userId=SAMPLE_VALID_OBJ_ID
        )
        delete_medication_use_case().execute.assert_called_with(
            delete_medication_request_object(
                session=session, user_id=SAMPLE_VALID_OBJ_ID
            )
        )


if __name__ == "__main__":
    unittest.main()
