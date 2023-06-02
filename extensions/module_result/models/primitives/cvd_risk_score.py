from enum import Enum

from extensions.module_result.common.enums import BiologicalSex
from sdk.common.utils.convertible import (
    convertibleclass,
    required_field,
    meta,
    default_field,
    ConvertibleClassValidationError,
)
from sdk.common.utils.validators import (
    str_to_bool,
    validate_hex_color,
    validate_range,
    round_to_half_int,
)
from .primitive import Primitive


class AlcoholIntake(Enum):
    DAILY = "DAILY"
    THREE_OR_FOUR_TIMES_A_WEEK = "THREE_OR_FOUR_TIMES_A_WEEK"
    ONCE_OR_TWICE_A_WEEK = "ONCE_OR_TWICE_A_WEEK"
    ONE_TO_THREE_TIMES_A_MONTH = "ONE_TO_THREE_TIMES_A_MONTH"
    SPECIAL_OCCASIONS = "SPECIAL_OCCASIONS"
    NEVER = "NEVER"


class WalkingPace(Enum):
    SLOW_PACE = "SLOW_PACE"
    STEADY_AVERAGE_PACE = "STEADY_AVERAGE_PACE"
    BRISK_PACE = "BRISK_PACE"


class OverallHealth(Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"


class ExistingCondition(Enum):
    HIGH_BLOOD_PRESSURE = "HIGH_BLOOD_PRESSURE"
    DIABETES = "DIABETES"
    ATRIAL_FIBRILLATION_OR_FLUTTER = "ATRIAL_FIBRILLATION_OR_FLUTTER"
    OTHER_HEART_ARRHYTHMIAS = "OTHER_HEART_ARRHYTHMIAS"
    DEPRESSION = "DEPRESSION"
    LEUKAEMIA_LYMPHOMA_MYELOMA = "LEUKAEMIA_LYMPHOMA_MYELOMA"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"


class ExistingSymptom(Enum):
    BREATHLESSNESS = "BREATHLESSNESS"
    DIZZINESS_OR_GIDDINESS = "DIZZINESS_OR_GIDDINESS"
    LOSS_OF_CONSCIOUSNESS_OR_COLLAPSE = "LOSS_OF_CONSCIOUSNESS_OR_COLLAPSE"
    ABDOMINAL_AND_PELVIC_PAIN = "ABDOMINAL_AND_PELVIC_PAIN"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"


class CurrentMedication(Enum):
    CHOLESTEROL_LOWERING_MEDICATION = "CHOLESTEROL_LOWERING_MEDICATION"
    BLOOD_PRESSURE_MEDICATION = "BLOOD_PRESSURE_MEDICATION"
    INSULIN = "INSULIN"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"


class FamilyHeartDisease(Enum):
    FATHER = "FATHER"
    MOTHER = "MOTHER"
    SIBLING = "SIBLING"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"


class RiskLabel(Enum):
    AGE = "Age"
    ALCOHOL = "Alcohol"
    BODY_MEASUREMENTS = "Body Measurements"
    HEALTH_RATING = "Health Rating"
    HEART_RATE = "Heart Rate"
    MEDICAL_HISTORY = "Medical History"
    PHYSICAL_ACTIVITY = "Physical Activity"
    SEX = "Sex"
    SLEEP = "Sleep"
    SMOKING = "Smoking"


@convertibleclass
class RiskFactor:
    PROTECTIVE_COLOR = "#FFDA9F"
    RISK_COLOR = "#FBCCD7"

    NAME = "name"
    CONTRIBUTION = "contribution"

    name: RiskLabel = required_field(metadata=meta(field_to_value=lambda x: x.value))
    colorHex: str = default_field(metadata=meta(validate_hex_color))
    contribution: float = default_field()

    def post_init(self):
        if self.contribution > 0:
            self.colorHex = self.RISK_COLOR
        elif self.contribution < 0:
            self.colorHex = self.PROTECTIVE_COLOR

    @property
    def status(self):
        return "Risk" if (self.contribution or 0) > 0 else "Protective"


@convertibleclass
class RiskTrajectory:
    DAYS_COUNT = "daysCount"
    RISK_PERCENTAGE = "riskPercentage"

    riskPercentage: float = required_field()
    daysCount: float = required_field()


@convertibleclass
class CVDRiskScore(Primitive):
    AGE = "age"
    SEX = "sex"
    HEART_RATE = "heartRate"
    WAIST_TO_HIP_RATIO = "waistToHipRatio"
    WAIST_CIRCUMFERENCE = "waistCircumference"
    HIP_CIRCUMFERENCE = "hipCircumference"
    CURRENT_MEDICATIONS = "currentMedications"
    EXISTING_SYMPTOMS = "existingSymptoms"
    EXISTING_CONDITIONS = "existingConditions"
    OVERALL_HEALTH = "overallHealth"
    WALKING_PACE = "walkingPace"
    ALCOHOL_INTAKE = "alcoholIntake"
    SLEEP_DURATION = "sleepDuration"
    SMOKING_STATUS = "smokingStatus"
    FAMILY_HEART_DISEASE = "familyHeartDisease"

    RISK_FACTORS = "riskFactors"
    RISK_TRAJECTORY = "riskTrajectory"
    ORIGINAL_VALUE = "originalValue"
    ROUNDED_VALUE = "roundedValue"

    age: float = required_field(metadata=meta(value_to_field=float))
    sex: BiologicalSex = required_field()
    alcoholIntake: AlcoholIntake = required_field()
    sleepDuration: float = required_field(metadata=meta(value_to_field=float))
    smokingStatus: bool = required_field(metadata=meta(value_to_field=str_to_bool))
    walkingPace: WalkingPace = required_field()
    overallHealth: OverallHealth = required_field()
    existingConditions: list[ExistingCondition] = required_field()
    existingSymptoms: list[ExistingSymptom] = required_field()
    currentMedications: list[CurrentMedication] = required_field()
    familyHeartDisease: list[FamilyHeartDisease] = required_field()
    heartRate: float = required_field(metadata=meta(value_to_field=round_to_half_int))
    waistCircumference: float = required_field(metadata=meta(value_to_field=float))
    hipCircumference: float = required_field(metadata=meta(value_to_field=float))
    waistToHipRatio: float = default_field(metadata=meta(value_to_field=float))

    riskFactors: list[RiskFactor] = default_field()
    riskTrajectory: list[RiskTrajectory] = default_field()
    originalValue: float = default_field(metadata=meta(value_to_field=float))
    roundedValue: float = default_field(
        metadata=meta(value_to_field=lambda x: round(x, 2))
    )

    def __iter__(self):
        excluded = [
            self.RISK_FACTORS,
            self.RISK_TRAJECTORY,
            self.originalValue,
            self.ROUNDED_VALUE,
        ]
        return (f for f in self.__annotations__ if f not in excluded)

    def items(self):
        return iter([(f, getattr(self, f)) for f in self])

    @classmethod
    def validate(cls, obj: "CVDRiskScore"):
        validators = {
            cls.HEART_RATE: validate_range(30, 174),
            cls.WAIST_CIRCUMFERENCE: validate_range(0, 500),
            cls.HIP_CIRCUMFERENCE: validate_range(0, 500),
            cls.SLEEP_DURATION: validate_range(1, 12),
        }
        for field, validator in validators.items():
            try:
                validator(getattr(obj, field))
            except Exception as error:
                raise ConvertibleClassValidationError(
                    f"Validation function error for [{field}] field with error [{error}]"
                )

    def post_init(self):
        waist_and_hip_present = self.waistCircumference and self.hipCircumference
        if waist_and_hip_present and not self.waistToHipRatio:
            waist_to_hip = self.waistCircumference / self.hipCircumference
            self.set_field_value(self.WAIST_TO_HIP_RATIO, waist_to_hip)
