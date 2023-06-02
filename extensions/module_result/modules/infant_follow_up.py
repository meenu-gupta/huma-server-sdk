from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import InfantFollowUp


class InfantFollowUpModule(AzModuleMixin, Module):
    moduleId = "InfantFollowUp"
    primitives = [InfantFollowUp]
