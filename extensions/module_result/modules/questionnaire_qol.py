from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import AdditionalQoL


class AdditionalQoLModule(AzModuleMixin, Module):
    moduleId = "AdditionalQoL"
    primitives = [AdditionalQoL]
