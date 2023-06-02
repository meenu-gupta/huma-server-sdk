from unittest import TestCase
from unittest.mock import MagicMock

from extensions.autocomplete.models.autocomplete_manager import (
    AutocompleteModulesManager,
)
from extensions.autocomplete.router.autocomplete_requests import (
    SearchAutocompleteRequestObject,
)
from extensions.autocomplete.use_cases.search_autocomplete_result_use_case import (
    SearchAutocompleteResultUseCase,
)
from sdk.common.utils import inject
from .test_helpers import get_sample_autocomplete_search_result_request_dict


class MockModule(MagicMock):
    retrieve_search_result = MagicMock()
    retrieve_search_result.return_value = ["Health status (2.4.1)"]


class MagicManager(MagicMock):
    retrieve_module = MagicMock()
    retrieve_module.return_value = MockModule()


class AutocompleteTests(TestCase):
    def setUp(self) -> None:
        def bind(binder):
            binder.bind(AutocompleteModulesManager, MagicManager)

        inject.clear_and_configure(bind)

    def test_success_search_autocomplete_result(self):
        request_object = SearchAutocompleteRequestObject.from_dict(
            get_sample_autocomplete_search_result_request_dict()
        )
        use_case = SearchAutocompleteResultUseCase()
        rsp = use_case.execute(request_object)
        self.assertEqual(["Health status (2.4.1)"], rsp.value)
