from extensions.export_deployment.helpers.convertion_helpers import (
    get_primitive_dict,
    ExportData,
)
from extensions.export_deployment.use_case.exportable.exportable_request_objects import (
    ExportableRequestObject,
)
from extensions.export_deployment.use_case.exportable.exportable_use_case import (
    ExportableUseCase,
)
from extensions.medication.models.medication import Medication
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.modules.module import Module


class MedicationsModuleExportableUseCase(ExportableUseCase):
    def get_raw_result(self) -> ExportData:
        module = self.get_module(self.request_object, "Medications")
        if not module:
            return {}

        raw_results = self.get_module_result(self.request_object, module)
        return {module.moduleId: [get_primitive_dict(p) for p in raw_results]}

    def get_module_result(
        self, request_object: ExportableRequestObject, module: Module
    ) -> list[Primitive]:
        module_results = []
        if module.exportable:
            module_primitives = module.primitives.copy()
            module_primitives.append(Medication)
            for primitive_cls in module_primitives:
                primitives = self._export_repo.retrieve_primitives(
                    primitive_class=primitive_cls,
                    module_id=module.moduleId,
                    deployment_id=request_object.deploymentId,
                    start_date=request_object.fromDate,
                    end_date=request_object.toDate,
                    user_ids=request_object.userIds,
                    use_creation_time=request_object.useCreationTime,
                )
                module_results.extend(primitives)
        return module_results
