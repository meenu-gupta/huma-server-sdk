from collections import defaultdict

from tomlkit._utils import merge_dicts

from extensions.export_deployment.helpers.convertion_helpers import (
    get_primitive_dict,
    get_object_fields,
    get_flatbuffer_fields,
    flat_questionnaire,
    ExportData,
)
from extensions.export_deployment.use_case.exportable.exportable_use_case import (
    ExportableUseCase,
)
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
)
from extensions.module_result.modules import (
    QuestionnaireModule,
    SymptomModule,
    MedicationTrackerModule,
    RevereTestModule,
    MedicationsModule,
)
from extensions.module_result.modules.licensed_questionnaire_module import (
    LicensedQuestionnaireModule,
)
from sdk.common.utils.common_functions_utils import get_all_subclasses


class ModuleExportableUseCase(ExportableUseCase):
    _modules_to_be_excluded = [
        QuestionnaireModule,
        SymptomModule,
        MedicationTrackerModule,
        RevereTestModule,
        MedicationsModule,
        LicensedQuestionnaireModule,
    ]

    def _get_excluded_module_names(self):
        modules = []
        for module in self._modules_to_be_excluded:
            modules.extend(get_all_subclasses(module))
        return [m.moduleId for m in modules]

    def get_raw_result(self) -> ExportData:
        # get list of module results
        excluded_modules = self.request_object.excludedModuleNames or []
        excluded_modules.extend(self._get_excluded_module_names())
        modules = self.get_modules(self.request_object.moduleNames, excluded_modules)

        raw_results = self.get_module_results(self.request_object, modules)

        final_results = defaultdict(list)
        for module_name, primitives in raw_results.items():
            for primitive in primitives:
                primitive_dict = get_primitive_dict(primitive)
                object_fields = get_object_fields(primitive)
                flatbuffer_fields = get_flatbuffer_fields(primitive)
                self.process_binaries(
                    primitive_dict,
                    self.request_object,
                    object_fields,
                    flatbuffer_fields,
                )

                meta_data = primitive_dict.get(Primitive.METADATA)
                answers = (meta_data or {}).get(QuestionnaireMetadata.ANSWERS, None)
                if self.request_object.useFlatStructure and answers:
                    module_config = self.get_module_config(
                        primitive, self.request_object.moduleConfigVersions
                    )
                    config_body = module_config.configBody if module_config else {}
                    flatten_answers = flat_questionnaire(
                        config_body,
                        answers,
                        self.request_object.extraQuestionIds,
                    )
                    del meta_data[QuestionnaireMetadata.ANSWERS]
                    merge_dicts(primitive_dict, flatten_answers)
                final_results[module_name].append(primitive_dict)

        return final_results
