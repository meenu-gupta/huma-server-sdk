from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import OtherVaccine


class OtherVaccineModule(AzModuleMixin, Module):
    moduleId = "OtherVaccine"
    primitives = [OtherVaccine]
