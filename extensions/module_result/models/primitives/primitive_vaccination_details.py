from datetime import date

from extensions.module_result.common.enums import (
    VaccineLocation,
    VaccineCategory,
    YesNoDont,
)
from extensions.module_result.common.questionnaire_utils import START_DATE_IN_2019
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    utc_date_to_str,
    utc_str_to_date,
    not_empty,
    validate_second_vaccine_schedule_date,
    validate_date_range,
)
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class OtherVaccCategoryItem:
    name: str = default_field()
    vaccDate: date = required_field(
        metadata=meta(
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )


@convertibleclass
class VaccinationDetails(SkippedFieldsMixin, Primitive):
    """VaccinationDetails model"""

    VACCINATED_PLACE = "vaccinatedPlace"
    VACCINATION_LOCATION = "vaccinationLocation"
    VACCINATION_CITY = "vaccinationCity"
    BATCH_NUMBER = "batchNumber"
    IS_BATCH_NUMBER_VALID = "isBatchNumberValid"
    IS_SECOND_DOSE_VACC = "isSecondDoseVacc"
    SECOND_VAC_SCHEDULE_DATE = "secondVacScheduleDate"
    IS_SEASON_FLU_VAC = "isSeasonFluVac"
    SEASON_FLU_VAC_DATE = "seasonFluVacDate"
    IS_OTHER_SPECIFIED_VACC = "isOtherSpecifiedVacc"
    OTHER_SPECIFIED_VACC = "otherSpecifiedVacc"
    OTHER_VACC_CATEGORY = "otherVaccCategory"
    IS_ALLERGIC_REACTION_VACC = "isAllergicReactionVacc"
    ALLERGIC_REACTION_VACC = "allergicReactionVacc"
    ALLERGIC_REACTION = "allergicReaction"
    METADATA = "metadata"

    FIELD_NAMES_TO_EXCLUDE = {IS_BATCH_NUMBER_VALID, SkippedFieldsMixin.SKIPPED}

    vaccinatedPlace: VaccineLocation = required_field()
    vaccinationLocation: str = default_field()
    vaccinationCity: str = required_field()
    batchNumber: str = required_field(metadata=meta(not_empty))
    isBatchNumberValid: bool = default_field()
    isSecondDoseVacc: YesNoDont = required_field()
    secondVacScheduleDate: date = default_field(
        metadata=meta(
            validator=validate_second_vaccine_schedule_date,
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    isSeasonFluVac: bool = required_field()
    seasonFluVacDate: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2019, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    isOtherSpecifiedVacc: bool = required_field()
    otherSpecifiedVacc: list[VaccineCategory] = default_field()
    otherVaccCategory: list[OtherVaccCategoryItem] = default_field()
    isAllergicReactionVacc: YesNoDont = required_field()
    allergicReactionVacc: list[str] = default_field()
    allergicReaction: list[str] = default_field()
    metadata: QuestionnaireMetadata = default_field()
