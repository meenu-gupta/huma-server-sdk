from extensions.module_result.router.module_result_requests import (
    SearchModuleResultsRequestObject,
)
from extensions.module_result.service.module_result_service import ModuleResultService
from extensions.module_result.use_cases.search_module_results_response_object import (
    SearchModuleResultsResponseObject,
)
from sdk.common.usecase.use_case import UseCase


class SearchModuleResultsUseCase(UseCase):
    def process_request(self, request_object: SearchModuleResultsRequestObject):
        # TODO move service logic here
        module_service = ModuleResultService()

        result_dict = {}
        for module_id in request_object.modules:
            result = module_service.retrieve_module_results(
                request_object.userId,
                module_id,
                request_object.skip,
                request_object.limit,
                request_object.direction,
                request_object.fromDateTime,
                request_object.toDateTime,
                request_object.filters,
                request_object.deploymentId,
                request_object.role,
            )
            result_dict.update(result)

        return SearchModuleResultsResponseObject(result_dict)
