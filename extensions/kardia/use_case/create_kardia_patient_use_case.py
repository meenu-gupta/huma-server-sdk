import logging

from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    UpdateUserProfileRequestObject,
)
from extensions.kardia.router.kardia_requests import CreateKardiaPatientRequestObject
from extensions.kardia.use_case.base_kardia_use_case import BaseKardiaUseCase
from sdk.common.usecase.response_object import Response
from sdk.common.utils.inject import autoparams

logger = logging.getLogger(__name__)


class CreateKardiaPatientUseCase(BaseKardiaUseCase):
    @autoparams()
    def __init__(self, auth_repo: AuthorizationRepository):
        super(CreateKardiaPatientUseCase, self).__init__()
        self._auth_repo = auth_repo

    def process_request(self, request_object: CreateKardiaPatientRequestObject):
        kardia_patient = self._kardia_integration_client.create_kardia_patient(
            request_object.email, request_object.dob
        )
        user_dict = {
            UpdateUserProfileRequestObject.ID: request_object.user.id,
            UpdateUserProfileRequestObject.KARDIA_ID: kardia_patient.get("id"),
            UpdateUserProfileRequestObject.PREVIOUS_STATE: request_object.user,
        }
        user = UpdateUserProfileRequestObject.from_dict(user_dict)
        user_id = self._auth_repo.update_user_profile(user)

        logger.info(f"Updated kardiaId {kardia_patient.get('id')} to user {user_id}")

        return Response(kardia_patient)
