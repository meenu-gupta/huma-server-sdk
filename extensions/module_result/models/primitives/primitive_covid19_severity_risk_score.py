"""model for Covid19SeverityRiskScore object"""
from datetime import datetime

from extensions.module_result.common.enums import (
    Ethnicity,
    Severity,
    BloodType,
    PreExistingCondition,
    CurrentSymptom,
    Covid19TestScore,
    Covid19TestType,
    BiologicalSex,
    SmokeStatus,
)
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import default_datetime_meta
from .primitive import Primitive


@convertibleclass
class Covid19SeverityRiskScore(Primitive):
    """
    Covid19SeverityRiskScore model
    """

    AGE = "age"
    WEIGHT = "weight"
    HEIGHT = "height"
    BIOLOGICAL_SEX = "biologicalSex"
    ETHNICITY = "ethnicity"
    SMOKE_STATUS = "smokeStatus"
    BLOOD_TYPE = "bloodType"
    PRE_EXISTING_CONDITIONS = "preExistingConditions"
    TEMPERATURE = "temperature"
    CURRENT_SYMPTOMS = "currentSymptoms"
    RESTING_BREATH_RATE = "restingBreathingRate"
    OXYGEN_SATURATION = "oxygenSaturation"
    RESTING_HEART_RATE = "restingHeartRate"

    covid19TestScore: Covid19TestScore = default_field()
    covid19TestDate: datetime = default_field(metadata=default_datetime_meta())
    covid19TestType: Covid19TestType = default_field()

    # 1.Baseline Parameters
    age: int = required_field(metadata=meta(value_to_field=int))
    # weight will be in KG
    weight: float = required_field(metadata=meta(value_to_field=float))
    # height will be in cm's
    height: float = required_field(metadata=meta(value_to_field=float))

    biologicalSex: BiologicalSex = required_field()
    ethnicity: Ethnicity = required_field()
    smokeStatus: SmokeStatus = required_field()
    bloodType: BloodType = required_field()
    symptomStartDateTime: datetime = default_field(metadata=default_datetime_meta())

    # 2.Pre Existing Conditions
    preExistingConditions: list[PreExistingCondition] = required_field()

    # 3.Current Symptoms
    temperature: float = required_field(metadata=meta(value_to_field=float))
    currentSymptoms: list[CurrentSymptom] = required_field()

    # 4.Vitals
    restingHeartRate: int = required_field(metadata=meta(value_to_field=int))
    restingBreathingRate: int = required_field(metadata=meta(value_to_field=int))
    oxygenSaturation: int = required_field(metadata=meta(value_to_field=int))

    # Calculated Result
    score: float = default_field(metadata=meta(value_to_field=float))
    # statuses = HIGH MODERATE LOW
    status: Severity = default_field()
