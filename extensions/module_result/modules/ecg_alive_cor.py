from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import ECGAliveCor


class ECGAliveCorModule(Module):
    moduleId = "ECGAliveCor"
    primitives = [ECGAliveCor]
