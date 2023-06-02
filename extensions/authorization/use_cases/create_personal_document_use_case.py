from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    CreatePersonalDocumentRequestObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class CreatePersonalDocumentUseCase(UseCase):
    @autoparams()
    def __init__(self, auth_repo: AuthorizationRepository):
        self._repo = auth_repo

    def process_request(self, request_object: CreatePersonalDocumentRequestObject):
        updated_id = self._repo.create_personal_document(
            user_id=request_object.userId,
            personal_doc=request_object.to_personal_document(),
        )
        return Response(value=updated_id)
