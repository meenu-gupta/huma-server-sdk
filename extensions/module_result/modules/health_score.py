from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import (
    AlcoholConsumption,
    BodyMeasurement,
    HeartRate,
    HScore,
    NumericMemory,
    ReactionTime,
    SelfHealthRate,
    SleepQuestions,
    SmokeQuestions,
    WaistToHeight,
    Weight,
)


class HealthScoreModule(Module):
    moduleId = "HealthScore"
    primitives = [
        BodyMeasurement,
        SelfHealthRate,
        WaistToHeight,
        Weight,
        HeartRate,
        SleepQuestions,
        SmokeQuestions,
        ReactionTime,
        AlcoholConsumption,
        NumericMemory,
        HScore,
    ]
