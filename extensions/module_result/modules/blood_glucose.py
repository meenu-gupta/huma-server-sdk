from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import BloodGlucose
from extensions.module_result.modules.visualizer import BloodGlucoseVisualizer


class BloodGlucoseModule(Module):
    moduleId = "BloodGlucose"
    primitives = [BloodGlucose]
    preferredUnitEnabled = True
    ragEnabled = True
    visualizer = BloodGlucoseVisualizer
