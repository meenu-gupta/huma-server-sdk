from extensions.module_result.common.enums import (
    BabyGender,
    GenderIdentity,
    Employment,
    SmokingStatus,
    SmokingStopped,
)
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import validate_range
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class BackgroundInformation(SkippedFieldsMixin, Primitive):
    AGE = "age"
    SEX_AT_BIRTH = "sexAtBirth"
    GENDER_IDENTITY = "genderIdentity"
    GENDER_OTHER = "genderOther"
    RESIDENCY_COUNTRY = "residenceCountry"
    BIRTH_COUNTRY = "birthCountry"
    WEIGHT = "weight"
    HEIGHT = "height"
    EMPLOYMENT = "employment"
    OTHER_EMPLOYMENT = "otherEmployment"
    IS_HEALTHCARE_WORKER = "isHealthcareWorker"
    SMOKING_STATUS = "smokingStatus"
    SMOKING_STOPPED = "smokingStopped"
    METADATA = "metadata"

    age: int = required_field(
        metadata=meta(validate_range(18, 120), value_to_field=int),
    )
    sexAtBirth: BabyGender = required_field()
    genderIdentity: GenderIdentity = required_field()
    genderOther: str = default_field()
    residenceCountry: str = required_field()
    birthCountry: str = required_field()
    weight: float = required_field(
        metadata=meta(validate_range(20, 300), value_to_field=float)
    )
    height: float = required_field(
        metadata=meta(validate_range(100, 250), value_to_field=float)
    )
    employment: Employment = required_field()
    otherEmployment: str = default_field()
    isHealthcareWorker: bool = default_field()
    smokingStatus: SmokingStatus = required_field()
    smokingStopped: SmokingStopped = default_field()
    metadata: QuestionnaireMetadata = required_field()
