"""model for Covid19SeverityRiskScore object"""
from extensions.module_result.common.enums import (
    Severity,
    BloodType,
    PreExistingCondition,
    CurrentSymptom,
)
from sdk.common.utils.convertible import convertibleclass, meta, default_field
from sdk.common.utils.convertible import required_field
from .primitive import Primitive


@convertibleclass
class Covid19RiskScoreCoreQuestions(Primitive):
    bloodType: BloodType = required_field()
    preExistingConditions: list[PreExistingCondition] = required_field()
    currentSymptoms: list[CurrentSymptom] = required_field()
    score: float = default_field(metadata=meta(value_to_field=float))
    status: Severity = default_field()
