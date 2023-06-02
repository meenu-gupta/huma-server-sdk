from pathlib import Path

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.modules.questionnaire import QuestionnaireModule
from extensions.module_result.models.primitives import Primitive, Questionnaire
from sdk.common.utils.validators import read_json_file


class SurgeryDetailsModule(QuestionnaireModule):
    moduleId = "SurgeryDetails"
    primitives = [Questionnaire]

    def get_validation_schema(self):
        return read_json_file(
            "./schemas/questionnaire_schema.json", Path(__file__).parent
        )

    def filter_results(
        self, primitives: list[Primitive], module_configs: list[ModuleConfig], **filters
    ) -> list[Primitive]:
        super().filter_results(primitives, module_configs, **filters)
        # returns only latest result, by default always requested DESCENDING order
        # on any issues logic should be changed to delete previous results
        # and always to keep only latest one
        return primitives[:1]
