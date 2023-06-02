from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import BreastFeedingStatus


class BreastFeedingStatusModule(AzModuleMixin, Module):
    moduleId = "BreastFeedingStatus"
    primitives = [BreastFeedingStatus]
