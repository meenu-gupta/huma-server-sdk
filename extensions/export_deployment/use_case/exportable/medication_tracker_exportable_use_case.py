from collections import defaultdict

from tomlkit._utils import merge_dicts

from extensions.export_deployment.helpers.convertion_helpers import (
    get_primitive_dict,
    flat_questionnaire,
    ExportData,
)
from extensions.export_deployment.use_case.exportable.exportable_use_case import (
    ExportableUseCase,
)


class MedicationTrackerModuleExportableUseCase(ExportableUseCase):
    def get_raw_result(self) -> ExportData:
        module = self.get_module(self.request_object, "MedicationTracker")
        if not module:
            return {}

        raw_results = self.get_module_result(self.request_object, module)

        final_results = defaultdict(list)

        for primitive in raw_results:
            primitive_dict = get_primitive_dict(primitive)

            questionnaire_name = module.moduleId
            if self.request_object.questionnairePerName:
                questionnaire_name = primitive_dict["questionnaireName"]

            if self.request_object.useFlatStructure:
                module_config = self.get_module_config(
                    primitive, self.request_object.moduleConfigVersions
                )
                config_body = module_config.configBody if module_config else {}
                flatten_data = flat_questionnaire(
                    config_body,
                    primitive_dict.pop("answers"),
                    self.request_object.extraQuestionIds,
                )
                merge_dicts(primitive_dict, flatten_data)

            final_results[questionnaire_name].append(primitive_dict)

        return final_results
