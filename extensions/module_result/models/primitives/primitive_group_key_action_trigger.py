from datetime import date
from enum import IntEnum

from sdk import meta, convertibleclass
from sdk.common.utils.convertible import required_field
from sdk.common.utils.validators import (
    utc_date_to_str,
    utc_str_to_date,
    validate_date_range,
)
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


class GroupCategory(IntEnum):
    PREGNANT = 0
    BREAST_FEEDING = 1
    BOTH_P_AND_B = 2
    FEMALE_LESS_50_NOT_P_OR_B = 3
    MALE_OR_FEMALE_OVER_50 = 4


@convertibleclass
class AZGroupKeyActionTrigger(SkippedFieldsMixin, Primitive):
    FIRST_VACCINE_DATE = "firstVaccineDate"
    GROUP_CATEGORY = "groupCategory"
    METADATA = "metadata"

    firstVaccineDate: date = required_field(
        metadata=meta(
            validate_date_range(end=lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    groupCategory: GroupCategory = required_field()
    metadata: QuestionnaireMetadata = required_field()
