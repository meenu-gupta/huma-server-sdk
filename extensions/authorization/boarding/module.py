from abc import ABC, abstractmethod

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import BoardingStatus
from extensions.deployment.models.deployment import OnboardingModuleConfig
from extensions.deployment.exceptions import OffBoardingRequiredError


class BoardingModule(ABC):
    name: str = ""
    has_onboarding: bool = None
    has_offboarding: bool = None
    onboarding_allowed_endpoints: tuple[str] = None

    def __init__(self, config: OnboardingModuleConfig = None):
        self.onboardingConfig = config

    @staticmethod
    @abstractmethod
    def validate_config_body(config_body: dict):
        raise NotImplementedError

    @abstractmethod
    def is_module_completed(self, authz_user: AuthorizedUser) -> bool:
        raise NotImplementedError

    def is_enabled(self, authz_user: AuthorizedUser) -> bool:
        return self.onboardingConfig and self.onboardingConfig.is_enabled()

    @abstractmethod
    def validate_if_allowed_to_reach_route(self, authz_user: AuthorizedUser, path: str):
        raise NotImplementedError

    @abstractmethod
    def check_if_user_off_boarded_and_raise_error(self, authz_user: AuthorizedUser):
        raise NotImplementedError

    def order(self):
        return self.onboardingConfig.order

    @staticmethod
    def check_if_user_already_off_boarded(
        authz_user: AuthorizedUser, expected_reason: BoardingStatus.ReasonOffBoarded
    ):
        user = authz_user.user
        if user.boardingStatus and user.boardingStatus.is_off_boarded():
            actual_reason = user.boardingStatus.reasonOffBoarded
            if actual_reason == expected_reason:
                raise OffBoardingRequiredError(
                    user.boardingStatus.get_reason_off_board_error_code()
                )
