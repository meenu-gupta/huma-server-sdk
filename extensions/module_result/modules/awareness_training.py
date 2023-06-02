from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import AwarenessTraining


class AwarenessTrainingModule(Module):
    moduleId = "AwarenessTraining"
    primitives = [AwarenessTraining]
