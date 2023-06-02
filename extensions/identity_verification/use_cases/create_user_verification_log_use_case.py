from flask import g

from extensions.authorization.models.user import User
from extensions.authorization.router.user_profile_request import (
    UpdateUserProfileRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.identity_verification.models.identity_verification import (
    OnfidoReportNameType,
)
from extensions.identity_verification.models.identity_verification_response import (
    CreateVerificationLogResponseObject,
)
from extensions.identity_verification.repository.verification_log_repository import (
    VerificationLogRepository,
)
from extensions.identity_verification.router.identity_verification_requests import (
    CreateVerificationLogRequestObject,
)
from sdk.common.adapter.identity_verification_adapter import IdentityVerificationCheck
from sdk.common.adapter.onfido.onfido_adapter import OnfidoAdapter
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig


class CreateVerificationLogUseCase(UseCase):
    ERROR_MSG = "ID verification in progress"

    @autoparams()
    def __init__(
        self,
        config: PhoenixServerConfig,
        adapter: OnfidoAdapter,
        deployment_repo: DeploymentRepository,
        verification_log_repo: VerificationLogRepository,
    ):
        self._config = config
        self._onfido_adapter = adapter
        self._deployment_repo = deployment_repo
        self._verification_log_repo = verification_log_repo

    def _create_check(self, applicant_id: str):
        data = {
            IdentityVerificationCheck.APPLICANT_ID: applicant_id,
            IdentityVerificationCheck.REPORT_NAMES: [
                OnfidoReportNameType.DOCUMENT.value,
                OnfidoReportNameType.FACIAL_SIMILARITY_PHOTO.value,
            ],
        }
        check = IdentityVerificationCheck.from_dict(remove_none_values(data))
        self._onfido_adapter.create_check(check)

    @staticmethod
    def _get_user(user_id: str) -> User:
        try:
            if g.user.id == user_id:
                return g.user
        except AttributeError:
            return AuthorizationService().retrieve_user_profile(user_id)

    def process_request(self, request_object: CreateVerificationLogRequestObject):
        user = self._get_user(request_object.userId)
        self._verification_log_repo.create_or_update_verification_log(request_object)
        self._update_user_status(user.id)
        self._create_check(user.onfidoApplicantId)
        return CreateVerificationLogResponseObject(self.ERROR_MSG)

    def _update_user_status(self, user_id):
        new_status = User.VerificationStatus.ID_VERIFICATION_IN_PROCESS.value
        data = {
            UpdateUserProfileRequestObject.ID: user_id,
            UpdateUserProfileRequestObject.VERIFICATION_STATUS: new_status,
        }
        request_obj = UpdateUserProfileRequestObject.from_dict(data)
        return AuthorizationService().update_user_profile(request_obj)
