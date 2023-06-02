from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import (
    Weight,
    Temperature,
    HeartRate,
    Covid19RiskScore,
    Covid19RiskScoreCoreQuestions,
    OxygenSaturation,
    RestingBreathingRate,
    SmokeQuestions,
)


class Covid19RiskScoreModule(Module):
    moduleId = "Covid19RiskScore"
    primitives = [
        Covid19RiskScoreCoreQuestions,
        Weight,
        SmokeQuestions,
        Temperature,
        HeartRate,
        RestingBreathingRate,
        OxygenSaturation,
        Covid19RiskScore,
    ]
