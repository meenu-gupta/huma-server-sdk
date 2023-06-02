from extensions.module_result.modules.module import Module
from extensions.module_result.modules.visualizer import MedicationVisualizer


class MedicationsModule(Module):
    moduleId = "Medications"
    primitives = []
    visualizer = MedicationVisualizer
