from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import RespiratoryRate


class RespiratoryRateModule(Module):
    moduleId = "RespiratoryRate"
    primitives = [RespiratoryRate]
    ragEnabled = True
