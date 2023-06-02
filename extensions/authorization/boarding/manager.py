from typing import Optional, Union

from extensions.authorization.boarding.manual_offboarding_module import (
    ManualOffBoardingModule,
)
from extensions.authorization.boarding.module import BoardingModule
from extensions.authorization.boarding.preferred_units_module import (
    PreferredUnitsModule,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import BoardingStatus
from extensions.authorization.router.user_profile_request import (
    FinishUserOnBoardingRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.common.exceptions import InvalidModuleException
from extensions.deployment.boarding.complete_study_tasks_module import (
    CompleteStudyTasksModule,
)
from extensions.deployment.boarding.consent_module import ConsentModule
from extensions.deployment.boarding.econsent_module import EConsentModule
from extensions.deployment.boarding.helper_agreement_module import HelperAgreementModule
from extensions.deployment.common import is_user_proxy_or_user_type
from extensions.deployment.exceptions import OffBoardingRequiredError
from extensions.deployment.models.deployment import OnboardingModuleConfig
from extensions.identity_verification.modules import IdentityVerificationModule
from extensions.module_result.boarding.az_screening_module import AZPScreeningModule


class BoardingManager:
    """Export, report, and file download urls are accessible for off-boarded
    users to enable them to download their own data.
    """

    PATH_WHITELIST = (
        "/device/register",
        "/device/unregister",
        "/configuration",
        "/user/<user_id>",
    )
    ALLOWED_PATHS_AFTER_OFF_BOARDING: tuple[str, ...] = (
        *PATH_WHITELIST,
        "/report/summary/user/<user_id>/task",
        "/export/user/<user_id>/task",
        "/signed/url/<bucket>/<path:filename>",
        "/export/user/<user_id>/task/<export_process_id>",
    )
    default_modules = (
        AZPScreeningModule,
        CompleteStudyTasksModule,
        ConsentModule,
        EConsentModule,
        HelperAgreementModule,
        IdentityVerificationModule,
        ManualOffBoardingModule,
        PreferredUnitsModule,
    )

    def __init__(self, authz_user: AuthorizedUser, path: str, url_rule):
        self.authz_user = authz_user
        self._deployment = self.authz_user.deployment
        self._enabled_boarding_modules: list[BoardingModule] = []
        self._setup_configs()
        self.path = path
        self.url_rule = str(url_rule)

    def check_off_boarding_and_raise_error(self):
        if not is_user_proxy_or_user_type(self.authz_user):
            return

        if self._check_skip_allowed(self.ALLOWED_PATHS_AFTER_OFF_BOARDING):
            return

        boarding_status = self.authz_user.user.boardingStatus
        if boarding_status and boarding_status.is_off_boarded():
            raise OffBoardingRequiredError(
                boarding_status.get_reason_off_board_error_code()
            )

        for module in self._enabled_boarding_modules:
            if not module.has_offboarding:
                continue
            module.check_if_user_off_boarded_and_raise_error(self.authz_user)

    def get_next_onboarding_task(self) -> Optional[str]:
        if not is_user_proxy_or_user_type(self.authz_user):
            return

        for module in self._enabled_boarding_modules:
            if not module.has_onboarding:
                continue
            if module.is_module_completed(self.authz_user):
                continue
            if not module.onboardingConfig:  # if module exists without config
                return module.name
            return module.onboardingConfig.id

        self.finish_onboarding()

    def check_on_boarding_and_raise_error(self):
        if self._check_skip_allowed(self.PATH_WHITELIST):
            return

        path_whitelist = []
        for module in self._enabled_boarding_modules:
            if module.onboarding_allowed_endpoints:
                path_whitelist.extend(module.onboarding_allowed_endpoints)

            if self._check_skip_allowed(tuple(path_whitelist)):
                return

            if not module.has_onboarding:
                continue

            module.validate_if_allowed_to_reach_route(self.authz_user, self.path)

    @classmethod
    def has(cls, module: Union[BoardingModule, str], raise_error=False) -> bool:
        module_exist = False
        if isinstance(module, BoardingModule):
            module_exist = module in cls.default_modules
        elif isinstance(module, str):
            module_exist = any(True for m in cls.default_modules if m.name == module)

        if not module_exist and raise_error:
            module_name = module if isinstance(module, str) else module.name
            raise InvalidModuleException(module_name)

        return module_exist

    def finish_onboarding(self):
        if self.authz_user.user.finishedOnboarding:
            return

        req_obj = FinishUserOnBoardingRequestObject.from_dict(
            {
                FinishUserOnBoardingRequestObject.ID: self.authz_user.id,
                FinishUserOnBoardingRequestObject.FINISHED_ONBOARDING: True,
                FinishUserOnBoardingRequestObject.BOARDING_STATUS: BoardingStatus(
                    status=BoardingStatus.Status.ACTIVE
                ),
                FinishUserOnBoardingRequestObject.PREVIOUS_STATE: self.authz_user.user,
            }
        )
        return AuthorizationService().update_user_profile(req_obj)

    def _setup_configs(self):
        modules = []
        configs = self._deployment.onboardingConfigs or []
        for module_cls in self.default_modules:
            module = module_cls(self._find_onboarding_config(configs, module_cls.name))
            if module.is_enabled(self.authz_user):
                modules.append(module)

        self._enabled_boarding_modules = sorted(modules, key=lambda x: x.order())

    @staticmethod
    def validate_onboarding_config_body(onboarding_id: str, onboarding_config: dict):
        module = BoardingManager._find_module(onboarding_id)
        if not module:
            raise InvalidModuleException(onboarding_id)
        module.validate_config_body(onboarding_config)

    @staticmethod
    def _find_module(onboarding_id: str):
        for module in BoardingManager.default_modules:
            if module.name == onboarding_id:
                return module

    @staticmethod
    def _find_onboarding_config(
        configs: list[OnboardingModuleConfig], onboarding_id: str
    ):
        return next(filter(lambda x: x.onboardingId == onboarding_id, configs), None)

    def _check_skip_allowed(self, path_whitelist: tuple[str, ...]):
        path_skip_allowed = self.path.endswith(path_whitelist)
        url_rule_skip_allowed = self.url_rule.endswith(path_whitelist)
        return any((path_skip_allowed, url_rule_skip_allowed))
