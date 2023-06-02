from dataclasses import field
from datetime import date

from extensions.module_result.common.enums import (
    PregnancyOutcome,
    BabyGender,
    ChildBirth,
    YesNoDont,
    BabyQuantity,
)
from extensions.module_result.common.questionnaire_utils import START_DATE_IN_2021
from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    utc_date_to_str,
    utc_str_to_date,
    validate_date_range,
    validate_range,
)
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class BabyInfo:
    PREGNANCY_FOR_BABY = "pregnancyForBaby"
    DATE_DELIVERY = "dateDelivery"
    PREGNANCY_DURATION = "pregnancyDuration"
    SPECIFIED_OUTCOME = "specifiedOutcome"
    BABY_GENDER = "babyGender"
    METHOD_DELIVERY = "methodDelivery"
    IS_BREAST_FEEDING_BABY = "isBreastfeedingBaby"
    IS_CURRENTLY_BREASTFEEDING_BABY = "isCurrentlyBreastfeedingBaby"
    BREASTFEED_LONG_TERM = "breastfeedLongTerm"
    IS_BABY_NO_LIQUID = "isBabyNoLiquid"
    IS_BABY_ISSUES = "isBabyIssues"
    SPECIFIED_ISSUES = "specifiedIssues"

    pregnancyForBaby: PregnancyOutcome = required_field()
    dateDelivery: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2021, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    pregnancyDuration: int = default_field(metadata=meta(validate_range(22, 45)))
    specifiedOutcome: list[str] = default_field()
    babyGender: BabyGender = default_field()
    methodDelivery: ChildBirth = default_field()
    isBreastfeedingBaby: bool = default_field()
    isCurrentlyBreastfeedingBaby: bool = default_field()
    breastfeedLongTerm: int = default_field(metadata=meta(validate_range(0, 110)))
    isBabyNoLiquid: bool = default_field()
    isBabyIssues: YesNoDont = default_field()
    specifiedIssues: list[str] = default_field()


@convertibleclass
class PregnancyFollowUp(SkippedFieldsMixin, Primitive):
    """Pregnancy follow up Questionnaire Model"""

    PREGNANCY_MEDICATION = "pregnantMedications"
    PRESCRIPTION_MEDICATIONS = "prescriptionMedications"
    OVER_COUNTER_PREGNANCY_MEDICATIONS = "overCounterPregnantMedications"
    OVER_COUNTER_MEDICATIONS = "overCounterMedications"
    BABY_COUNT = "babyCount"
    CURRENT_BABY_COUNT = "currentBabyCount"
    BABY_INFO = "babyInfo"
    METADATA = "metadata"

    pregnantMedications: bool = required_field()
    prescriptionMedications: list[str] = default_field()
    overCounterPregnantMedications: bool = required_field()
    overCounterMedications: list[str] = default_field()
    babyCount: BabyQuantity = required_field()
    currentBabyCount: int = default_field()
    babyInfo: list[BabyInfo] = required_field()
    metadata: QuestionnaireMetadata = required_field()
