from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import OxygenSaturation
from .visualizer import OxygenSaturationVisualizer


class OxygenSaturationModule(Module):
    moduleId = "OxygenSaturation"
    primitives = [OxygenSaturation]
    ragEnabled = True
    visualizer = OxygenSaturationVisualizer
