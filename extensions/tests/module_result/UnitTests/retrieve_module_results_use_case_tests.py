import unittest
from unittest.mock import MagicMock, patch

from extensions.module_result.router.module_result_requests import (
    RetrieveModuleResultRequestObject,
)
from extensions.module_result.use_cases.retrieve_module_results_use_case import (
    RetrieveModuleResultUseCase,
)

MODULE_RESULTS_USE_CASE = (
    "extensions.module_result.use_cases.retrieve_module_results_use_case"
)
SAMPLE_VALID_OBJ_ID = "60a20766c85cd55b38c99e12"


class RetrieveModuleResultUseCaseTestCase(unittest.TestCase):
    @patch(f"{MODULE_RESULTS_USE_CASE}.PostRetrievePrimitiveEvent")
    @patch(f"{MODULE_RESULTS_USE_CASE}.DeploymentService")
    def test_success_retrieve_module_result_use_case(self, _, post_event):
        module_result_repo = MagicMock()
        module_result_repo.retrieve_primitive.return_value = MagicMock()
        event_bus = MagicMock()
        use_case = RetrieveModuleResultUseCase(
            repo=module_result_repo, event_bus=event_bus
        )
        primitive_type = "test_primitive_type"
        req_obj = RetrieveModuleResultRequestObject.from_dict(
            {
                RetrieveModuleResultRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID,
                RetrieveModuleResultRequestObject.MODULE_RESULT_ID: SAMPLE_VALID_OBJ_ID,
                RetrieveModuleResultRequestObject.PRIMITIVE_TYPE: primitive_type,
            }
        )
        use_case.execute(req_obj)
        module_result_repo.retrieve_primitive.assert_called_with(
            SAMPLE_VALID_OBJ_ID, primitive_type, SAMPLE_VALID_OBJ_ID
        )
        post_event.from_primitive.assert_called_with(
            module_result_repo.retrieve_primitive()
        )


if __name__ == "__main__":
    unittest.main()
