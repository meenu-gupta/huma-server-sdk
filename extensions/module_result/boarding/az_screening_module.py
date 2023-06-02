import logging
from typing import Optional

from extensions.authorization.boarding.module import BoardingModule
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import BoardingStatus
from extensions.common.sort import SortField
from extensions.deployment.exceptions import DeploymentErrorCodes
from extensions.deployment.models.deployment import OnboardingModuleConfig
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.exceptions import OnboardingError
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.modules.az_screening_questionnaire import (
    AZScreeningQuestionnaireModule,
)
from extensions.module_result.modules.module import Module
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from sdk.common.exceptions.exceptions import InvalidModuleConfigBody
from sdk.common.utils import inject

logger = logging.getLogger(__name__)


class AZPScreeningModule(BoardingModule):
    name: str = "AZScreeningOnboarding"
    onboardingConfig: OnboardingModuleConfig = None
    has_onboarding: bool = True
    has_offboarding: bool = True
    onboarding_allowed_endpoints: tuple[str] = (
        f"/module-result/{AZScreeningQuestionnaireModule.moduleId}",
    )

    @staticmethod
    def validate_config_body(config_body: dict):
        if config_body:
            msg = f"Config body for {AZPScreeningModule.name} should be empty"
            raise InvalidModuleConfigBody(msg)

    def is_module_completed(self, authz_user: AuthorizedUser) -> bool:
        if self._search_az_screening_module(authz_user):
            return True
        return False

    def validate_if_allowed_to_reach_route(self, authz_user: AuthorizedUser, path: str):
        if not self._search_az_screening_module(authz_user):
            raise OnboardingError(
                config_id=AZPScreeningModule.name,
                code=DeploymentErrorCodes.AZ_PRESCREENING_NEEDED,
            )

    def _search_az_screening_module(
        self, authz_user: AuthorizedUser
    ) -> Optional[list[Primitive]]:
        repo = inject.instance(ModuleResultRepository)
        module = self._get_az_screening_module()

        for module_primitive in module.primitives:
            module_results = repo.retrieve_primitives(
                user_id=authz_user.id,
                module_id=AZScreeningQuestionnaireModule.moduleId,
                primitive_name=module_primitive.__name__,
                skip=0,
                limit=1,
                direction=SortField.Direction.ASC,
            )
            return module_results

    def _get_az_screening_module(self) -> Module:
        deployment_service = DeploymentService()
        return deployment_service.retrieve_module(
            module_id=AZScreeningQuestionnaireModule.moduleId
        )

    def check_if_user_off_boarded_and_raise_error(self, authz_user: AuthorizedUser):
        self.check_if_user_already_off_boarded(
            authz_user, BoardingStatus.ReasonOffBoarded.USER_FAIL_PRE_SCREENING
        )
