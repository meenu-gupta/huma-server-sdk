from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import Temperature


class TemperatureModule(Module):
    moduleId = "Temperature"
    primitives = [Temperature]
    preferredUnitEnabled = True
    ragEnabled = True
