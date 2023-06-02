from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import (
    RestingBreathingRate,
)


class RestingBreathingRateModule(Module):
    moduleId = "RestingBreathingRate"
    primitives = [RestingBreathingRate]
