from datetime import datetime

import isodate

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User, BoardingStatus
from extensions.authorization.boarding.module import BoardingModule
from extensions.authorization.router.user_profile_request import (
    SystemOffBoardUserRequestObject,
)
from extensions.authorization.use_cases.off_board_user_use_case import (
    OffBoardUserUseCase,
)
from extensions.deployment.exceptions import (
    OffBoardingRequiredError,
    DeploymentErrorCodes,
)


class CompleteStudyTasksModule(BoardingModule):
    name: str = "CompleteStudy"
    has_offboarding: bool = True
    has_onboarding: bool = False

    def order(self):
        if self.onboardingConfig:
            return self.onboardingConfig.order
        return 999

    def is_enabled(self, authz_user: AuthorizedUser) -> bool:
        return True

    @staticmethod
    def validate_config_body(config_body: dict):
        pass

    def is_module_completed(self, authz_user: AuthorizedUser) -> bool:
        pass

    def validate_if_allowed_to_reach_route(self, authz_user: AuthorizedUser, path: str):
        pass

    def check_if_user_off_boarded_and_raise_error(self, authz_user: AuthorizedUser):
        self.check_if_user_already_off_boarded(
            authz_user, BoardingStatus.ReasonOffBoarded.USER_COMPLETE_ALL_TASK
        )
        deployment = authz_user.deployment
        if deployment.features and not deployment.features.offBoarding:
            return

        if deployment.duration:
            if self.is_user_expired(authz_user.user, deployment.duration):
                off_board_reason = (
                    BoardingStatus.ReasonOffBoarded.USER_COMPLETE_ALL_TASK
                )
                OffBoardUserUseCase().execute(
                    SystemOffBoardUserRequestObject.from_dict(
                        {
                            SystemOffBoardUserRequestObject.USER_ID: authz_user.user.id,
                            SystemOffBoardUserRequestObject.REASON: off_board_reason,
                        }
                    )
                )
                raise OffBoardingRequiredError(
                    DeploymentErrorCodes.OFF_BOARDING_USER_COMPLETE_ALL_TASK
                )

    @staticmethod
    def is_user_expired(user: User, duration):
        """Check if user has reached clinician study expiration date."""
        deployment_duration = isodate.parse_duration(duration)
        if user.boardingStatus and not user.boardingStatus.is_off_boarded():
            start_time = user.boardingStatus.updateDateTime
        else:
            start_time = user.createDateTime
        expiration_date = start_time + deployment_duration
        if expiration_date <= datetime.utcnow():
            return True
