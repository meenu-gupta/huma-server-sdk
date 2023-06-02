from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import Weight


class WeightModule(Module):
    moduleId = "Weight"
    primitives = [Weight]
    preferredUnitEnabled = True
    ragEnabled = True
