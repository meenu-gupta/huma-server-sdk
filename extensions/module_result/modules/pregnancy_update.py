from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import PregnancyUpdate


class PregnancyUpdateModule(AzModuleMixin, Module):
    moduleId = "PregnancyUpdate"
    primitives = [PregnancyUpdate]
