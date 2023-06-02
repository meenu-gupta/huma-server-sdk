from extensions.module_result.common.enums import BeforeAfter
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    validate_days_took_medication_before_vaccination,
    validate_days_took_medication_after_vaccination,
    validate_days_took_medication,
)
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class FeverAndPainDrugs(SkippedFieldsMixin, Primitive):
    """FeverAndPainDrugs model"""

    HAS_ANTI_FEVER_PAIN_DRUGS = "hasAntiFeverPainDrugs"
    MED_STARTED_BEFORE_AFTER = "medStartedBeforeAfter"
    DAYS_BEFORE_VAC_MEDICATION = "daysBeforeVacMedication"
    DAYS_AFTER_VAC_MEDICATION = "daysAfterVacMedication"
    IS_UNDER_MEDICATION = "isUnderMedication"
    DAYS_COUNT_MEDICATION = "daysCountMedication"
    METADATA = "metadata"

    hasAntiFeverPainDrugs: bool = required_field()
    medStartedBeforeAfter: BeforeAfter = default_field()
    daysBeforeVacMedication: int = default_field(
        metadata=meta(validate_days_took_medication_before_vaccination),
    )
    daysAfterVacMedication: int = default_field(
        metadata=meta(validate_days_took_medication_after_vaccination),
    )
    isUnderMedication: bool = default_field()
    daysCountMedication: int = default_field(
        metadata=meta(validate_days_took_medication)
    )
    metadata: QuestionnaireMetadata = required_field()
