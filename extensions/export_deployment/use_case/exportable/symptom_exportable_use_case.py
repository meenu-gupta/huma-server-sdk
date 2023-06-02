from tomlkit._utils import merge_dicts

from extensions.export_deployment.helpers.convertion_helpers import (
    get_primitive_dict,
    flat_symptoms,
    ExportData,
)
from extensions.export_deployment.use_case.exportable.exportable_use_case import (
    ExportableUseCase,
)


class SymptomModuleExportableUseCase(ExportableUseCase):
    def get_raw_result(self) -> ExportData:
        module = self.get_module(self.request_object, "Symptom")
        if not module:
            return {}

        raw_results = self.get_module_result(self.request_object, module)

        final_results = {}

        for primitive in raw_results:
            if module.moduleId not in final_results:
                final_results[module.moduleId] = []
            primitive_dict = get_primitive_dict(primitive)

            if self.request_object.useFlatStructure and len(primitive_dict) > 0:
                module_config = self.get_module_config(
                    primitive, self.request_object.moduleConfigVersions
                )
                config_body = module_config.configBody if module_config else {}
                merge_dicts(primitive_dict, flat_symptoms(config_body, primitive_dict))

            final_results[module.moduleId].append(primitive_dict)

        return final_results
