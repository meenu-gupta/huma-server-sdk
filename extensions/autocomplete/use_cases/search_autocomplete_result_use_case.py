from extensions.autocomplete.models.autocomplete_manager import (
    AutocompleteModulesManager,
)
from extensions.autocomplete.router.autocomplete_requests import (
    SearchAutocompleteRequestObject,
)
from sdk.common.exceptions.exceptions import DetailedException, ErrorCodes
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class SearchAutocompleteResultUseCase(UseCase):
    @autoparams()
    def __init__(self, manager: AutocompleteModulesManager):
        self.manager = manager

    def process_request(self, request_object: SearchAutocompleteRequestObject):
        module_id = request_object.listEndpointId
        module = self.manager.retrieve_module(module_id)
        if not module:
            error = f"Invalid value {module_id} for autocomplete module name"
            raise DetailedException(ErrorCodes.INVALID_AUTOCOMPLETE_ENDPOINT, error)

        result = module.retrieve_search_result(
            search_key=request_object.search,
            exact_word=request_object.exactWord,
            language=request_object.language,
        )
        return Response(result)
