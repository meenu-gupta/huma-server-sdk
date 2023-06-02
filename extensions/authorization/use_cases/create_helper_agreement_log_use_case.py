from extensions.authorization.models.helper_agreement_log import HelperAgreementLog
from extensions.authorization.models.user import BoardingStatus
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    CreateHelperAgreementLogRequestObject,
    SystemOffBoardUserRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.authorization.use_cases.off_board_user_use_case import (
    OffBoardUserUseCase,
)
from extensions.deployment.exceptions import (
    OffBoardingRequiredError,
    DeploymentErrorCodes,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class CreateHelperAgreementLogUseCase(UseCase):
    @autoparams()
    def __init__(self, auth_repo: AuthorizationRepository):
        self._repo = auth_repo
        self._service = AuthorizationService()

    def process_request(
        self, request_object: CreateHelperAgreementLogRequestObject
    ) -> Response:

        if request_object.status == HelperAgreementLog.Status.DO_NOT_AGREE:
            off_board_reason = (
                BoardingStatus.ReasonOffBoarded.USER_FAIL_HELPER_AGREEMENT
            )
            OffBoardUserUseCase().execute(
                SystemOffBoardUserRequestObject.from_dict(
                    {
                        SystemOffBoardUserRequestObject.USER_ID: self.request_object.userId,
                        SystemOffBoardUserRequestObject.REASON: off_board_reason,
                    }
                )
            )
            raise OffBoardingRequiredError(
                DeploymentErrorCodes.OFF_BOARDING_USER_FAIL_HELPER_AGREEMENT
            )

        updated_id = self._repo.create_helper_agreement_log(
            helper_agreement_log=request_object
        )
        return Response(value=updated_id)
