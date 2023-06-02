from datetime import date

from extensions.module_result.common.enums import VaccineCategory
from extensions.module_result.common.questionnaire_utils import START_DATE_IN_2021
from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    utc_date_to_str,
    utc_str_to_date,
    validate_date_range,
)
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class VaccineListItem:
    NAME = "name"
    VACCINATED_DATE = "vaccinatedDate"

    name: str = required_field()
    vaccinatedDate: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2021, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )


@convertibleclass
class OtherVaccine(SkippedFieldsMixin, Primitive):
    """OtherVaccine model"""

    HAS_FLU_VACCINE = "hasFluVaccine"
    FLU_VACCINE_DATE = "fluVaccineDate"
    HAS_OTHER_VACCINE = "hasOtherVaccine"
    VACCINE_CATEGORY = "vaccineCategory"
    VACCINE_LIST = "vaccineList"
    UNKNOWN_VACCINE_DATE = "unknownVaccineDate"
    METADATA = "metadata"

    hasFluVaccine: bool = required_field(default=False)
    fluVaccineDate: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2021, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    hasOtherVaccine: bool = required_field(default=False)
    vaccineCategory: list[VaccineCategory] = default_field()
    vaccineList: list[VaccineListItem] = default_field()
    metadata: QuestionnaireMetadata = required_field()
