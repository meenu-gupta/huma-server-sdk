from extensions.autocomplete.repository.autocomplete_repository import (
    AutoCompleteRepository,
)
from extensions.autocomplete.router.autocomplete_requests import (
    UpdateAutoCompleteSearchMetadataRequestObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class UpdateAutoCompleteMetadataUseCase(UseCase):
    @autoparams()
    def __init__(self, autocomplete_repo: AutoCompleteRepository):
        self.autocomplete_repo = autocomplete_repo

    def process_request(
        self, request_object: UpdateAutoCompleteSearchMetadataRequestObject
    ):
        ids = []
        for m in request_object.metadata:
            ids.append(str(self.autocomplete_repo.update_autocomplete_metadata(m)))

        return Response(value=ids)
