from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import HealthStatus


class HealthStatusModule(AzModuleMixin, Module):
    moduleId = "HealthStatus"
    primitives = [HealthStatus]
    ragEnabled = True
