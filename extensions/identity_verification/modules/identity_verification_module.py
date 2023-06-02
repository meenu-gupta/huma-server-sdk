import logging

from extensions.authorization.boarding.module import BoardingModule
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User, BoardingStatus
from extensions.authorization.router.user_profile_request import (
    SystemOffBoardUserRequestObject,
)
from extensions.authorization.use_cases.off_board_user_use_case import (
    OffBoardUserUseCase,
)
from extensions.common.exceptions import InvalidIdentityReportNameException
from extensions.deployment.exceptions import (
    OffBoardingRequiredError,
    DeploymentErrorCodes,
)
from extensions.deployment.models.deployment import OnboardingModuleConfig
from extensions.exceptions import OnboardingError
from extensions.identity_verification.models.identity_verification import (
    OnfidoReportNameType,
)
from sdk.common.exceptions.exceptions import (
    IdVerificationInProgressException,
    IdVerificationNeededException,
    InvalidModuleConfigBody,
)

logger = logging.getLogger(__name__)


class IdentityVerificationModule(BoardingModule):
    REQUIRED_REPORTS = "requiredReports"
    CONFIGURATION_BLOCKER_STATUSES = (
        User.VerificationStatus.ID_VERIFICATION_IN_PROCESS,
        User.VerificationStatus.ID_VERIFICATION_FAILED,
    )
    VERIFICATION_ERRORS = {
        None: IdVerificationNeededException,
        User.VerificationStatus.ID_VERIFICATION_FAILED: OffBoardingRequiredError,
        User.VerificationStatus.ID_VERIFICATION_IN_PROCESS: IdVerificationInProgressException,
        User.VerificationStatus.ID_VERIFICATION_NEEDED: IdVerificationNeededException,
        User.VerificationStatus.ID_VERIFICATION_SUCCEEDED: None,
    }
    onboarding_allowed_endpoints: tuple[str] = (
        "/generate-identity-verification-sdk-token",
        "/user-verification-log",
    )

    name: str = "IdentityVerification"
    onboardingConfig: OnboardingModuleConfig = None
    has_offboarding: bool = True
    has_onboarding: bool = True

    @staticmethod
    def validate_config_body(config_body: dict):
        if config_body:
            required_reports = config_body.get(
                IdentityVerificationModule.REQUIRED_REPORTS
            )
            if required_reports:
                if isinstance(required_reports, list):
                    for report in required_reports:
                        if not OnfidoReportNameType.has_value(report):
                            raise InvalidIdentityReportNameException(report)
                else:
                    msg = f"[{IdentityVerificationModule.REQUIRED_REPORTS}] should be list type"
                    raise InvalidModuleConfigBody(msg)

    def is_module_completed(self, authz_user: AuthorizedUser) -> bool:
        status = authz_user.user.verificationStatus
        if status != User.VerificationStatus.ID_VERIFICATION_SUCCEEDED.value:
            return False
        return True

    def validate_if_allowed_to_reach_route(self, authz_user: AuthorizedUser, path: str):
        status = authz_user.user.verificationStatus
        if status not in self.CONFIGURATION_BLOCKER_STATUSES:
            return

        error = self.VERIFICATION_ERRORS.get(authz_user.user.verificationStatus)
        if error and error != OffBoardingRequiredError:
            raise OnboardingError(self.name, error().code)

    def check_if_user_off_boarded_and_raise_error(self, authz_user: AuthorizedUser):
        self.check_if_user_already_off_boarded(
            authz_user, BoardingStatus.ReasonOffBoarded.USER_FAIL_ID_VERIFICATION
        )
        error = self.VERIFICATION_ERRORS.get(authz_user.user.verificationStatus)
        if error == OffBoardingRequiredError:
            off_board_reason = BoardingStatus.ReasonOffBoarded.USER_FAIL_ID_VERIFICATION
            OffBoardUserUseCase().execute(
                SystemOffBoardUserRequestObject.from_dict(
                    {
                        SystemOffBoardUserRequestObject.USER_ID: authz_user.user.id,
                        SystemOffBoardUserRequestObject.REASON: off_board_reason,
                    }
                )
            )
            raise error(DeploymentErrorCodes.OFF_BOARDING_USER_FAIL_ID_VERIFICATION)
