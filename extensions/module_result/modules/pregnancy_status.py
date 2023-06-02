from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import PregnancyStatus


class PregnancyStatusModule(AzModuleMixin, Module):
    moduleId = "PregnancyStatus"
    primitives = [PregnancyStatus]
