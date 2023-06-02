from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import Height


class HeightModule(Module):
    moduleId = "Height"
    primitives = [Height]
    preferredUnitEnabled = True
    ragEnabled = True
