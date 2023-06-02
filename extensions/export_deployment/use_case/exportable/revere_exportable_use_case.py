import os

from extensions.export_deployment.helpers.convertion_helpers import (
    get_primitive_dict,
    get_object_fields,
    get_flatbuffer_fields,
    ExportData,
)
from extensions.export_deployment.use_case.exportable.exportable_request_objects import (
    ExportableRequestObject,
)
from extensions.export_deployment.use_case.exportable.exportable_use_case import (
    ExportableUseCase,
)
from extensions.module_result.models.primitives import Primitive
from extensions.revere.models.revere import RevereTest, RevereTestResult
from extensions.revere.service.revere_service import RevereTestService


class RevereExportableUseCase(ExportableUseCase):
    def get_raw_result(self) -> ExportData:
        module = self.get_module(self.request_object, "RevereTest")
        if not module:
            return {}

        raw_results = self.get_module_result(
            self.request_object,
            module,
        )

        final_results = {}

        for primitive in raw_results:
            if module.moduleId not in final_results:
                final_results[module.moduleId] = []
            primitive_dict = get_primitive_dict(primitive)
            object_fields = get_object_fields(primitive)
            flatbuffer_fields = get_flatbuffer_fields(primitive)
            self.process_binaries(
                primitive_dict, self.request_object, object_fields, flatbuffer_fields
            )

            final_results[module.moduleId].append(primitive_dict)

        return final_results

    def process_binaries(
        self,
        raw_dict: dict,
        request_object: ExportableRequestObject,
        object_fields: list,
        flatbuffer_fields: list,
    ):
        test_id = raw_dict[RevereTest.ID]
        user_id = raw_dict[RevereTest.USER_ID]
        test_csv_data = RevereTestService(fs=self._file_storage).export_test_result(
            user_id, test_id
        )
        export_dir = f"{request_object.exportDir}/{self.build_binary_path(request_object, raw_dict)}"
        os.makedirs(export_dir, exist_ok=True)
        with open(f"{export_dir}/{test_id}.csv", "w") as result_file:
            result_file.write(test_csv_data)
        for test_result in raw_dict[RevereTest.RESULTS]:
            test_result[RevereTestResult.CLS] = RevereTestResult.__name__
            super().process_binaries(
                raw_dict=test_result,
                request_object=request_object,
                object_fields=[RevereTestResult.AUDIO_RESULT],
                flatbuffer_fields=[],
            )

    def get_module_config(self, primitive: Primitive, module_configs_versions: dict):
        pass
