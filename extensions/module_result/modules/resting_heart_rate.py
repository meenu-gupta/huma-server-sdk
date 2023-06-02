from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import HeartRate


class RestingHeartRateModule(Module):
    moduleId = "RestingHeartRate"
    primitives = [HeartRate]
    ragEnabled = True
