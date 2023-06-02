from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import BreastFeedingUpdate


class BreastFeedingUpdateModule(AzModuleMixin, Module):
    moduleId = "BreastFeedingUpdate"
    primitives = [BreastFeedingUpdate]
