from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import BoardingStatus
from extensions.authorization.boarding.module import BoardingModule


class ManualOffBoardingModule(BoardingModule):
    name: str = "ManualOffBoarding"
    has_onboarding: bool = False
    has_offboarding: bool = True

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
            authz_user, BoardingStatus.ReasonOffBoarded.USER_MANUAL_OFF_BOARDED
        )
