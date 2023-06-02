from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import MedicalHistory


class MedicalHistoryModule(AzModuleMixin, Module):
    moduleId = "MedicalHistory"
    primitives = [MedicalHistory]
