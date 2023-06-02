from typing import Optional
from extensions.authorization.models.user import User
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives.primitive import Primitive
from extensions.module_result.models.primitives import EQ5D5L, Questionnaire
from extensions.module_result.modules.licensed_questionnaire_module import (
    LicensedQuestionnaireModule,
)
from extensions.module_result.questionnaires.eq5d_questionnaire_calculator import (
    EQ5DQuestionnaireCalculator,
)
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils.common_functions_utils import find

TOGGLE_INDEX_VALUE = "toggleIndexValue"


class EQ5D5LModule(LicensedQuestionnaireModule):
    moduleId = "EQ5D5L"
    primitives = [Questionnaire, EQ5D5L]
    calculator = EQ5DQuestionnaireCalculator
    partitioned_answers: dict
    ragEnabled = True

    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        if len(primitives) > 1:
            raise InvalidRequestException("Only one questionnaire can be submitted")

        questionnaire = primitives[0]
        if not isinstance(questionnaire, Questionnaire):
            raise InvalidRequestException("Only questionnaire can be submitted")

        eq5d5l_data = {
            **questionnaire.to_dict(include_none=False),
        }
        eq5d5l = EQ5D5L.from_dict(eq5d5l_data)
        eq5d5l.scoring_answers = questionnaire.answers
        primitives.append(eq5d5l)
        return super().preprocess(primitives, user)

    def change_primitives_based_on_config(
        self, primitives: list[Primitive], module_configs: list[ModuleConfig]
    ):
        if not module_configs or not primitives:
            return
        for primitive in primitives:
            if type(primitive) is not EQ5D5L:
                continue
            module_config = find(
                lambda x: x.id == primitive.moduleConfigId, module_configs
            )
            if not module_config:
                continue
            config_body = module_config.get_config_body()
            if not config_body.get(TOGGLE_INDEX_VALUE):
                primitive.indexValue = None
