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


class EConsentModule(BoardingModule):
    name: str = "EConsent"
    onboardingConfig: OnboardingModuleConfig = None
    has_offboarding: bool = True
    has_onboarding: bool = True
    onboarding_allowed_endpoints: tuple[str] = (
        "/econsent",
        "/sign",
        "/upload/<bucket>",
        "/signed/url/<bucket>/<path:filename>",
    )

    def order(self):
        if self.onboardingConfig:
            return self.onboardingConfig.order
        return 3

    def is_enabled(self, authz_user: AuthorizedUser) -> bool:
        if not authz_user.get_econsent():
            return False

        if self.onboardingConfig:
            return self.onboardingConfig.is_enabled()
        return True

    @staticmethod
    def validate_config_body(config_body: dict):
        if config_body:
            msg = f"Config body for {EConsentModule.name} should be empty"
            raise InvalidModuleConfigBody(msg)

    def is_module_completed(self, authz_user: AuthorizedUser) -> bool:
        return self.is_econsent_signed(authz_user)

    def validate_if_allowed_to_reach_route(self, authz_user: AuthorizedUser, path: str):
        if not authz_user.is_user():
            return

        if not self.is_econsent_signed(authz_user):
            raise OnboardingError(
                config_id=EConsentModule.name,
                code=DeploymentErrorCodes.ECONSENT_NOT_SIGNED,
            )

    def check_if_user_off_boarded_and_raise_error(self, authz_user: AuthorizedUser):
        self.check_if_user_already_off_boarded(
            authz_user, BoardingStatus.ReasonOffBoarded.USER_UNSIGNED_EICF
        )

    @staticmethod
    def is_econsent_signed(auth_user: AuthorizedUser) -> bool:
        service = DeploymentService()
        return service.is_econsent_signed(auth_user.id, auth_user.deployment)
