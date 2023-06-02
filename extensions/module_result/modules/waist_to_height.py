from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import WaistToHeight


class WaistToHeightModule(Module):
    moduleId = "WaistToHeight"
    primitives = [WaistToHeight]
