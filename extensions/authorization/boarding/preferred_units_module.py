import logging
from typing import Set

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.deployment.models.deployment import Deployment
from extensions.exceptions import OnboardingError
from extensions.deployment.exceptions import DeploymentErrorCodes
from extensions.authorization.boarding.module import BoardingModule
from extensions.module_result.modules import WeightModule, HeightModule, BMIModule

logger = logging.getLogger(__name__)


class PreferredUnitsModule(BoardingModule):
    name: str = "PreferredUnits"
    has_onboarding: bool = True
    has_offboarding: bool = False
    onboarding_allowed_endpoints = ("user/<user_id>",)

    @staticmethod
    def validate_config_body(config_body: dict):
        if config_body:
            msg = f"Config body for {PreferredUnitsModule.name} should be empty"
            raise Exception(msg)

    def is_module_completed(self, authz_user: AuthorizedUser) -> bool:
        return self._user_submitted_all_preferred_units(authz_user)

    def validate_if_allowed_to_reach_route(self, authz_user: AuthorizedUser, path: str):
        if not self._user_submitted_all_preferred_units(authz_user):
            raise OnboardingError(
                config_id=PreferredUnitsModule.name,
                code=DeploymentErrorCodes.PREFERRED_UNITS_MODULE_NEEDED,
            )

    def check_if_user_off_boarded_and_raise_error(self, authz_user: AuthorizedUser):
        pass

    def _user_submitted_all_preferred_units(self, authz_user: AuthorizedUser) -> bool:
        user_preferred_units = authz_user.user.preferredUnits
        if not user_preferred_units:
            return False

        enabled_modules = self._get_enabled_modules_with_preferred_units(
            authz_user.deployment
        )
        return enabled_modules.issubset(user_preferred_units.keys())

    @staticmethod
    def _get_enabled_modules_with_preferred_units(
        deployment: Deployment,
    ) -> Set[str]:
        from extensions.module_result.modules.modules_manager import ModulesManager

        module_configs = deployment.moduleConfigs
        enabled_modules_in_deployment = {
            i.moduleId for i in module_configs if i.is_enabled()
        }
        if (
            deployment.profile
            and deployment.profile.fields
            and deployment.profile.fields.height
        ):
            enabled_modules_in_deployment.add(HeightModule.moduleId)

        if BMIModule.moduleId in enabled_modules_in_deployment:
            enabled_modules_in_deployment.add(WeightModule.moduleId)

        modules_with_preferred_units = (
            ModulesManager().get_preferred_unit_enabled_module_ids()
        )

        return enabled_modules_in_deployment.intersection(modules_with_preferred_units)
