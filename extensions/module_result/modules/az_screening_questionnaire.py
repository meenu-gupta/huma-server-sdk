from typing import Optional

from extensions.authorization.models.user import User, BoardingStatus
from extensions.authorization.router.user_profile_request import (
    SystemOffBoardUserRequestObject,
)
from extensions.authorization.use_cases.off_board_user_use_case import (
    OffBoardUserUseCase,
)
from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.deployment.exceptions import (
    OffBoardingRequiredError,
    DeploymentErrorCodes,
)
from extensions.module_result.models.primitives import (
    AZScreeningQuestionnaire,
    Primitive,
)


class AZScreeningQuestionnaireModule(AzModuleMixin, Module):
    moduleId = "AZScreeningQuestionnaire"
    primitives = [AZScreeningQuestionnaire]

    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        for primitive in primitives:
            if type(primitive) == AZScreeningQuestionnaire:
                answers_yes = (
                    primitive.hasReceivedCOVIDVacInPast4Weeks,
                    primitive.isAZVaccineFirstDose,
                    primitive.is18YearsOldDuringVaccination,
                )
                if not all(answers_yes):
                    off_board_reason = (
                        BoardingStatus.ReasonOffBoarded.USER_FAIL_PRE_SCREENING
                    )
                    OffBoardUserUseCase().execute(
                        SystemOffBoardUserRequestObject.from_dict(
                            {
                                SystemOffBoardUserRequestObject.USER_ID: user.id,
                                SystemOffBoardUserRequestObject.REASON: off_board_reason,
                            }
                        )
                    )
                    raise OffBoardingRequiredError(
                        DeploymentErrorCodes.OFF_BOARDING_USER_FAIL_PRE_SCREENING
                    )
