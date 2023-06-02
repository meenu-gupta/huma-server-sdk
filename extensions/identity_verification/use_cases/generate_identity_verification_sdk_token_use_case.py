from datetime import datetime, timedelta

from extensions.authorization.models.user import User
from extensions.authorization.router.user_profile_request import (
    UpdateUserProfileRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.identity_verification.models.identity_verification_sdk_token_response import (
    IdentityVerificationSdkTokenResponse,
)
from extensions.identity_verification.router.identity_verification_requests import (
    GenerateIdentityVerificationTokenRequestObject,
)
from sdk.common.adapter.identity_verification_adapter import (
    IdentityVerificationApplicant,
)

from sdk.common.adapter.onfido.onfido_adapter import OnfidoAdapter
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.common.usecase.response_object import Response
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig


class GenerateIdentityVerificationSdkTokenUseCase(UseCase):
    request_object: GenerateIdentityVerificationTokenRequestObject = None

    @autoparams()
    def __init__(
        self,
        config: PhoenixServerConfig,
        adapter: OnfidoAdapter,
        deployment_repo: DeploymentRepository,
    ):
        self._config = config
        self._onfido_adapter = adapter
        self._deployment_repo = deployment_repo

    def execute(self, request_object):
        self.request_object = request_object
        return super().execute(request_object)

    def _create_applicant(self, user: User) -> str:
        user_data = {
            IdentityVerificationApplicant.FIRST_NAME: self.request_object.legalFirstName,
            IdentityVerificationApplicant.LAST_NAME: self.request_object.legalLastName,
            IdentityVerificationApplicant.DOB: user.dateOfBirth,
            IdentityVerificationApplicant.EMAIL: user.email,
            IdentityVerificationApplicant.ADDRESS: user.addressComponent,
        }
        user_data = remove_none_values(user_data)
        applicant = IdentityVerificationApplicant.from_dict(user_data)
        return self._onfido_adapter.create_applicant(applicant)

    def _create_or_get_applicant_id(self, user: User) -> str:
        if user.onfidoApplicantId:
            return user.onfidoApplicantId

        applicant_id = self._create_applicant(user)
        data = {
            UpdateUserProfileRequestObject.ID: user.id,
            UpdateUserProfileRequestObject.ONFIDO_APPLICANT_ID: applicant_id,
            UpdateUserProfileRequestObject.PREVIOUS_STATE: user,
        }
        request_obj = UpdateUserProfileRequestObject.from_dict(data)
        AuthorizationService().update_user_profile(request_obj)
        return applicant_id

    def process_request(
        self, request_object: GenerateIdentityVerificationTokenRequestObject
    ):
        user = AuthorizationService().retrieve_user_profile(
            user_id=request_object.userId
        )
        applicant_id = self._create_or_get_applicant_id(user)
        sdk_token = self._onfido_adapter.generate_sdk_token(
            applicant_id,
            request_object.applicationId,
        )

        expire_datetime = datetime.utcnow() + timedelta(
            minutes=self._config.server.adapters.onfido.tokenExpiresAfterMinutes
        )
        response = IdentityVerificationSdkTokenResponse.from_dict(
            {
                IdentityVerificationSdkTokenResponse.APPLICANT_ID: applicant_id,
                IdentityVerificationSdkTokenResponse.TOKEN: sdk_token,
                IdentityVerificationSdkTokenResponse.UTC_EXPIRATION_DATE_TIME: expire_datetime,
            }
        )
        return Response(value=response)
