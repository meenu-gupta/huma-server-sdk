from dataclasses import field
from datetime import date

from extensions.module_result.common.enums import HealthIssueAction, NewSymptomAction
from extensions.module_result.common.questionnaire_utils import START_DATE_IN_2020
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
class BreastFeedingUpdateBabyDetails:
    HEALTH_ISSUE = "healthIssue"
    HEALTH_ISSUE_ACTION = "healthIssueAction"
    HAS_RECEIVED_DIAGNOSIS = "hasReceivedDiagnosis"
    DIAGNOSIS_LIST = "diagnosisList"

    healthIssue: list[str] = required_field()
    healthIssueAction: list[HealthIssueAction] = required_field()
    hasReceivedDiagnosis: bool = required_field()
    diagnosisList: list[str] = default_field()


@convertibleclass
class BreastFeedingUpdate(SkippedFieldsMixin, Primitive):
    IS_BREASTFEEDING_NOW = "isBreastFeedingNow"
    STOP_DATE = "stopDate"
    NOW_OR_WORSE_SYMPTOM = "newOrWorseSymptoms"
    BREASTFEEDING_BABY_DETAILS = "breastFeedingBabyDetails"
    NUM_BREASTFEEDING_BABIES = "numBreastFeedingBabies"
    METADATA = "metadata"

    isBreastFeedingNow: bool = required_field()
    stopDate: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2020, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    newOrWorseSymptoms: list[NewSymptomAction] = required_field()
    numBreastFeedingBabies: int = field(default=0, metadata=meta(validate_range(0, 3)))
    breastFeedingBabyDetails: list[BreastFeedingUpdateBabyDetails] = default_field()
    metadata: QuestionnaireMetadata = required_field()
