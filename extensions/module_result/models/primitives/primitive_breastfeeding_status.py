from dataclasses import field

from extensions.module_result.common.enums import YesNoDont
from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import validate_range
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class BreastFeedingBabyStatusDetailsItem:
    AGE_IN_MONTHS = "ageInMonths"
    HAS_ONLY_BREAST_MILK = "hasOnlyBreastMilk"
    WEIGHT_AT_BIRTH = "weightAtBirth"
    IS_BREAST_FEEDING_CURRENTLY = "isBreastFeedingCurrently"
    HAS_BIRTH_DEFECT = "hasBirthDefects"
    BABY_BIRTH_DEFECT_LIST = "babyBirthDefectList"
    HAS_CHRONIC_CONDITION = "hasChronicConditions"
    CHRONIC_CONDITION_LIST = "chronicConditionList"
    HAS_MEDICATIONS = "hasMedications"
    IS_MEDICATION_BY_DOCTOR = "isMedicationByDoctor"
    CONDITION_LIST = "conditionList"

    ageInMonths: int = required_field(metadata=meta(validate_range(1, 36)))
    hasOnlyBreastMilk: bool = default_field()
    weightAtBirth: float = required_field(
        metadata=meta(validate_range(1, 10), value_to_field=float),
    )
    hasBirthDefects: bool = required_field()
    babyBirthDefectList: list[str] = default_field()
    hasChronicConditions: bool = required_field()
    chronicConditionList: list[str] = default_field()
    hasMedications: bool = required_field()
    isMedicationByDoctor: bool = default_field()
    conditionList: list[str] = default_field()


@convertibleclass
class BreastFeedingStatus(SkippedFieldsMixin, Primitive):
    IS_BREASTFEEDING_CURRENTLY = "isBreastFeedingCurrently"
    NUMBER_OF_WEEKS_AT_CHILD_BIRTH = "numberOfWeeksAtChildBirth"
    HAD_COMPLICATIONS_AT_BIRTH = "hadComplicationsAtBirth"
    COMPLICATION_LIST = "complicationList"
    HAS_RISK_CONDITIONS = "hasHighRiskConditions"
    HIGH_RISK_CONDITIONS = "highRiskConditions"
    FAMILY_HISTORY_OF_DEFECTS = "familyHistoryOfDefects"
    FAMILY_HISTORY_OF_DEFECTS_LIST = "familyHistoryOfDefectsList"
    NUM_BREASTFEEDING_BABIES = "numBreastFeedingBabies"
    BREASTFEEDING_BABY_DETAILS = "breastFeedingBabyDetails"
    METADATA = "metadata"

    isBreastFeedingCurrently: bool = required_field()
    numberOfWeeksAtChildBirth: int = default_field()
    hadComplicationsAtBirth: bool = default_field()
    complicationList: list[str] = default_field()
    hasHighRiskConditions: bool = default_field()
    highRiskConditions: list[str] = default_field()
    familyHistoryOfDefects: YesNoDont = default_field()
    familyHistoryOfDefectsList: list[str] = default_field()
    numBreastFeedingBabies: int = field(default=0, metadata=meta(validate_range(0, 3)))
    breastFeedingBabyDetails: list[BreastFeedingBabyStatusDetailsItem] = default_field()
    metadata: QuestionnaireMetadata = required_field()
