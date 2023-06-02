from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import HighFrequencyStep


class HighFrequencyStepModule(Module):
    moduleId = "HighFrequencyStep"
    primitives = [HighFrequencyStep]

    @property
    def exportable(self):
        return False
