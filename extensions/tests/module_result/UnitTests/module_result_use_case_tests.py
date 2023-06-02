from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from extensions.module_result.router.module_result_requests import (
    SearchModuleResultsRequestObject,
)
from extensions.module_result.use_cases.search_module_results_use_case import (
    SearchModuleResultsUseCase,
)

SAMPLE_USER_ID = "5fe07f2c0d862378d70fa19b"
SAMPLE_DEPLOYMENT_ID = "5fe0a9c0d4696db1c7cd759a"


class MockAuthUser:
    def __init__(self, user):
        self.user = user


class MockModuleResultService:
    retrieve_module_results = MagicMock()


class TestSearchModuleResultUseCase(TestCase):
    @patch(
        f"extensions.module_result.use_cases.search_module_results_use_case.ModuleResultService",
        MockModuleResultService,
    )
    def test_success_search_module_results(self):
        request_object = SearchModuleResultsRequestObject.from_dict(
            {
                "modules": ["first_id", "second_id"],
                "userId": SAMPLE_USER_ID,
                "deploymentId": SAMPLE_DEPLOYMENT_ID,
                "role": "role",
            }
        )
        SearchModuleResultsUseCase().execute(request_object)
        calls = [
            call(
                SAMPLE_USER_ID,
                "second_id",
                None,
                None,
                None,
                None,
                None,
                None,
                SAMPLE_DEPLOYMENT_ID,
                "role",
            ),
            call(
                SAMPLE_USER_ID,
                "first_id",
                None,
                None,
                None,
                None,
                None,
                None,
                SAMPLE_DEPLOYMENT_ID,
                "role",
            ),
        ]

        MockModuleResultService.retrieve_module_results.assert_has_calls(
            calls, any_order=True
        )
        self.assertEqual(MockModuleResultService.retrieve_module_results.call_count, 2)
