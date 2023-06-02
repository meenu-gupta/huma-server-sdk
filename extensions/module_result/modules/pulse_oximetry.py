from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import PulseOximetry


class PulseOximetryModule(Module):
    moduleId = "PulseOximetry"
    primitives = [PulseOximetry]
    ragEnabled = True
