from datetime import date

from extensions.module_result.common.enums import BrandOfVaccine, PlaceOfVaccination
from sdk import meta, convertibleclass
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import utc_date_to_str, utc_str_to_date, not_empty
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class PostVaccination(SkippedFieldsMixin, Primitive):

    SECOND_COVID_VACCINATION_DOSE = "secondCOVIDVaccinationDose"
    IS_SECOND_DOSE_AZ = "isSecondDoseAZ"
    SECOND_DOSE_BRAND = "secondDoseBrand"
    BATCH_NUMBER_VACCINE = "batchNumberVaccine"
    IS_SAME_PLACE_VACCINE_2_AS_1 = "isSamePlaceVaccine2As1"
    VACCINATION_PLACE = "vaccinationPlace"
    VACCINATION_PLACE_OTHER = "vaccinationPlaceOther"
    VACCINATION_PLACE_LOCATION = "vaccinationPlaceLocation"
    IS_BATCH_NUMBER_VALID = "isBatchNumberValid"
    METADATA = "metadata"

    FIELD_NAMES_TO_EXCLUDE = {IS_BATCH_NUMBER_VALID, SkippedFieldsMixin.SKIPPED}

    secondCOVIDVaccinationDose: date = required_field(
        metadata=meta(
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    isSecondDoseAZ: bool = required_field()
    secondDoseBrand: BrandOfVaccine = default_field()
    batchNumberVaccine: str = default_field(metadata=meta(not_empty))
    isBatchNumberValid: bool = default_field()
    isSamePlaceVaccine2As1: bool = required_field()
    vaccinationPlace: PlaceOfVaccination = default_field()
    vaccinationPlaceOther: str = default_field(metadata=meta(not_empty))
    vaccinationPlaceLocation: str = default_field(metadata=meta(not_empty))
    metadata: QuestionnaireMetadata = required_field()
