from extensions.module_result.repository.custom_module_config_repository import (
    CustomModuleConfigRepository,
)
from extensions.module_result.router.custom_module_config_requests import (
    RetrieveCustomModuleConfigsRequestObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrieveCustomModuleConfigsUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: CustomModuleConfigRepository):
        self._repo = repo

    def process_request(self, request_object: RetrieveCustomModuleConfigsRequestObject):
        configs = self._repo.retrieve_custom_module_configs(
            user_id=request_object.user_id
        )
        return Response(value=configs)
