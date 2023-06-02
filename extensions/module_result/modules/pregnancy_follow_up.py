from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import PregnancyFollowUp


class PregnancyFollowUpModule(AzModuleMixin, Module):
    moduleId = "PregnancyFollowUp"
    primitives = [PregnancyFollowUp]
