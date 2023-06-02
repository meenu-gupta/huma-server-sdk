from extensions.authorization.models.user import PersonalDocument
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    RetrievePersonalDocumentsRequestObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrievePersonalDocumentsUseCase(UseCase):
    @autoparams()
    def __init__(self, auth_repo: AuthorizationRepository):
        self._repo = auth_repo

    def process_request(
        self, request_object: RetrievePersonalDocumentsRequestObject
    ) -> Response:
        documents: list[PersonalDocument] = self._repo.retrieve_personal_documents(
            user_id=request_object.userId
        )
        return Response(documents)
