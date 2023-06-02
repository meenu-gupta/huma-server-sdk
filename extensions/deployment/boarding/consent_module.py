import logging

from extensions.authorization.boarding.module import BoardingModule
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import BoardingStatus
from extensions.deployment.exceptions import DeploymentErrorCodes
from extensions.deployment.models.deployment import OnboardingModuleConfig
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.exceptions import OnboardingError
from sdk.common.exceptions.exceptions import InvalidModuleConfigBody

logger = logging.getLogger(__name__)


class ConsentModule(BoardingModule):
    name: str = "Consent"
    onboardingConfig: OnboardingModuleConfig = None
    has_offboarding: bool = False
    has_onboarding: bool = True
    onboarding_allowed_endpoints: tuple[str] = (
        "/consent",
        "/sign",
        "/upload/<bucket>",
        "/signed/url/<bucket>/<path:filename>",
    )

    def order(self):
        if self.onboardingConfig:
            return self.onboardingConfig.order
        return 1

    def is_enabled(self, authz_user: AuthorizedUser) -> bool:
        if not authz_user.get_consent():
            return False

        if self.onboardingConfig:
            return self.onboardingConfig.is_enabled()
        return True

    @property
    def off_boarding_reason(self) -> BoardingStatus.ReasonOffBoarded:
        return BoardingStatus.ReasonOffBoarded.USER_NO_CONSENT

    @staticmethod
    def validate_config_body(config_body: dict):
        if config_body:
            msg = f"Config body for {ConsentModule.name} should be empty"
            raise InvalidModuleConfigBody(msg)

    def is_module_completed(self, authz_user: AuthorizedUser) -> bool:
        return self.is_consent_signed(authz_user)

    def validate_if_allowed_to_reach_route(self, authz_user: AuthorizedUser, path: str):
        if not authz_user.is_user():
            return

        if not self.is_consent_signed(authz_user):
            raise OnboardingError(
                config_id=ConsentModule.name,
                code=DeploymentErrorCodes.CONSENT_NOT_SIGNED,
            )

    def check_if_user_off_boarded_and_raise_error(self, authz_user: AuthorizedUser):
        pass

    @staticmethod
    def is_consent_signed(auth_user: AuthorizedUser) -> bool:
        service = DeploymentService()
        return service.is_consent_signed(auth_user.id, auth_user.deployment)
