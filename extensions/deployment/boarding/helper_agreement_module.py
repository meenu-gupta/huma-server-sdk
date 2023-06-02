import logging

from extensions.authorization.boarding.module import BoardingModule
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.helper_agreement_log import HelperAgreementLog
from extensions.authorization.models.user import BoardingStatus
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.exceptions import DeploymentErrorCodes
from extensions.deployment.models.deployment import OnboardingModuleConfig
from extensions.exceptions import OnboardingError
from sdk.common.exceptions.exceptions import InvalidModuleConfigBody
from sdk.common.utils import inject

logger = logging.getLogger(__name__)


class HelperAgreementModule(BoardingModule):
    name: str = "HelperAgreement"
    onboardingConfig: OnboardingModuleConfig = None
    has_offboarding: bool = True
    has_onboarding: bool = True
    onboarding_allowed_endpoints: tuple[str] = ("/helperagreementlog",)

    def order(self):
        if self.onboardingConfig:
            return self.onboardingConfig.order
        return 999

    @staticmethod
    def validate_config_body(config_body: dict):
        if config_body:
            msg = f"Config body for {HelperAgreementModule.name} should be empty"
            raise InvalidModuleConfigBody(msg)

    def is_module_completed(self, authz_user: AuthorizedUser) -> bool:
        return bool(self._search_for_helper_agreement_logs(authz_user))

    def validate_if_allowed_to_reach_route(self, authz_user: AuthorizedUser, path: str):
        if not self._search_for_helper_agreement_logs(authz_user):
            raise OnboardingError(
                config_id=HelperAgreementModule.name,
                code=DeploymentErrorCodes.HELPER_AGREEMENT_NEEDED,
            )

    @staticmethod
    def _search_for_helper_agreement_logs(
        authz_user: AuthorizedUser,
    ) -> HelperAgreementLog:
        repo = inject.instance(AuthorizationRepository)

        return repo.retrieve_helper_agreement_log(
            user_id=authz_user.id, deployment_id=authz_user.deployment.id
        )

    def check_if_user_off_boarded_and_raise_error(self, authz_user: AuthorizedUser):
        self.check_if_user_already_off_boarded(
            authz_user, BoardingStatus.ReasonOffBoarded.USER_FAIL_HELPER_AGREEMENT
        )
