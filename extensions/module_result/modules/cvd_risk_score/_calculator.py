from typing import Union

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire
from extensions.module_result.models.primitives.cvd_risk_score import (
    CVDRiskScore,
    RiskFactor,
    RiskTrajectory,
    RiskLabel,
)
from extensions.module_result.modules.cvd_risk_score.ai_cvd_model import (
    CVDRiskScoreRequestObject,
    AIRiskTrajectory,
    AIRiskFactor,
    CVDRiskScoreResponseObject,
)
from extensions.module_result.questionnaires import QuestionnaireCalculator
from ._config import CVDRiskScoreConfig
from .service import AIScoringService


class CVDRiskScoreCalculator(QuestionnaireCalculator):
    def __init__(self, config: CVDRiskScoreConfig = None):
        self.config = config or CVDRiskScoreConfig()

    def calculate(
        self,
        primitive: Union[CVDRiskScore, Questionnaire],
        module_config: ModuleConfig,
    ):
        if not isinstance(primitive, CVDRiskScore):
            return

        cvd_risk_score = primitive

        score = self.get_score(cvd_risk_score)

        self._set_risk_factor(cvd_risk_score, score.riskFactors)
        self._set_risk_trajectory(cvd_risk_score, score.riskTrajectory)
        cvd_risk_score.set_field_value(CVDRiskScore.ORIGINAL_VALUE, score.risk)
        cvd_risk_score.set_field_value(CVDRiskScore.ROUNDED_VALUE, score.risk)

    def get_score(self, cvd_risk_score: CVDRiskScore) -> CVDRiskScoreResponseObject:
        req_obj = CVDRiskScoreRequestObject.from_primitive(cvd_risk_score)
        return AIScoringService().get_cvd_risk_score(req_obj)

    def _set_risk_factor(self, data: CVDRiskScore, source: list[AIRiskFactor]):
        def to_risk_factor(labeled_score: tuple[str, float]):
            name, score = labeled_score
            src = {RiskFactor.NAME: name, RiskFactor.CONTRIBUTION: score}
            return RiskFactor.from_dict(src)

        grouped_factors = self._group_risk_factors(source)
        risk_factors = [to_risk_factor(score) for score in grouped_factors.items()]
        data.set_field_value(field=CVDRiskScore.RISK_FACTORS, field_value=risk_factors)

    @staticmethod
    def _set_risk_trajectory(data: CVDRiskScore, source: list[AIRiskTrajectory]):
        def to_risk_trajectory(trj: AIRiskTrajectory):
            src = {
                RiskTrajectory.RISK_PERCENTAGE: trj.risk,
                RiskTrajectory.DAYS_COUNT: trj.days,
            }
            return RiskTrajectory.from_dict(src)

        data.set_field_value(
            field=CVDRiskScore.RISK_TRAJECTORY,
            field_value=[to_risk_trajectory(trj) for trj in source],
        )

    def _group_risk_factors(self, risk_factors: list[AIRiskFactor]) -> dict[str, float]:
        groups = {
            RiskLabel.AGE.value: "Age",
            RiskLabel.SEX.value: "Sex",
            RiskLabel.SMOKING.value: "Being a smoker",
            RiskLabel.BODY_MEASUREMENTS.value: [
                "Waist circumference",
                "Hip circumference",
                "Waist-to-hip ratio",
            ],
            RiskLabel.HEART_RATE.value: "Heart rate",
            RiskLabel.MEDICAL_HISTORY: [
                "Diagnosis of atrial fibrillation and flutter",
                "Diagnosis of haematological cancer",
                "Diagnosis of depressive episode",
                "Diagnosis of other cardiac arrhythmias",
                "Diagnosis of diabetes",
                "Diagnosis of hypertension",
                "Shortness of breath",
                "Abdominal or pelvic pain",
                "Dizziness of giddiness",
                "Fainting or collapse",
                "Taking cholesterol medications",
                "Taking blood pressure medications",
                "Taking insulin",
                "Taking cholesterol medications",
                "Father diagnosed with heart disease",
                "Mother diagnosed with heart disease",
                "Sibling diagnosed with heart disease",
            ],
            RiskLabel.HEALTH_RATING.value: "Self-rated health",
            RiskLabel.PHYSICAL_ACTIVITY.value: "Walking pace",
            RiskLabel.SLEEP.value: ["Short sleep duration", "Good sleep duration"],
        }

        risk_score_buffer = {name: 0.0 for name in groups}

        for factor in risk_factors:
            for name, labels in groups.items():
                if factor.label in labels:
                    risk_score_buffer[name] += factor.contribution

        return risk_score_buffer
