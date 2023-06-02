from extensions.authorization.models.user import User
from extensions.module_result.models.primitives import (
    BodyMeasurement,
    HeartRate,
    Primitive,
    Questionnaire,
)
from extensions.module_result.models.primitives.cvd_risk_score import CVDRiskScore
from extensions.module_result.modules.module import Module
from ._calculator import CVDRiskScoreCalculator
from ._preprocessor import CVDRiskScorePreprocessor
from ..visualizer import CardiovascularHTMLVisualizer


class CVDRiskScoreModule(Module):
    moduleId = "CVDRiskScore"
    primitives = [Questionnaire, CVDRiskScore, HeartRate, BodyMeasurement]
    calculator = CVDRiskScoreCalculator
    visualizer = CardiovascularHTMLVisualizer

    def preprocess(self, primitives: list[Primitive], user: User):
        CVDRiskScorePreprocessor(user).run(primitives)

    def calculate(self, primitive: Questionnaire):
        if not isinstance(primitive, CVDRiskScore):
            return

        self.calculator().calculate(primitive, self.config)
