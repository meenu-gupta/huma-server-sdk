from sdk.common.utils.convertible import convertibleclass, required_field
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class AZScreeningQuestionnaire(SkippedFieldsMixin, Primitive):
    """AZScreeningQuestionnaire model."""

    HAS_RECEIVED_COVID_VAC_IN_PAST_4_WEEKS = "hasReceivedCOVIDVacInPast4Weeks"
    IS_AZ_VAC_FIRST_DOSE = "isAZVaccineFirstDose"
    IS_18_Y_OLD_DURING_VAC = "is18YearsOldDuringVaccination"
    METADATA = "metadata"

    hasReceivedCOVIDVacInPast4Weeks: bool = required_field()
    isAZVaccineFirstDose: bool = required_field()
    is18YearsOldDuringVaccination: bool = required_field()
    metadata: QuestionnaireMetadata = required_field()
