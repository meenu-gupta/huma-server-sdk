from datetime import date

from extensions.module_result.common.enums import (
    YesNoDont,
    CovidTestResult,
    CovidTestType,
    HealthIssueAction,
    YesNoNa,
    SymptomIntensity,
    NewSymptomAction,
)
from extensions.module_result.common.questionnaire_utils import START_DATE_IN_2021
from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    utc_date_to_str,
    utc_str_to_date,
    validate_range,
    validate_date_range,
)
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class SymptomsListItem:
    NAME = "name"
    INTENSITY = "intensity"
    START_DATE = "startDate"
    IS_RESOLVED = "isResolved"
    END_DATE = "endDate"

    name: str = required_field()
    intensity: SymptomIntensity = required_field()
    startDate: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2021, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    isResolved: bool = required_field()
    endDate: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2021, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )


@convertibleclass
class CovidTestListItem:
    METHOD = "method"
    DATE = "date_"
    OTHER_METHOD_NAME = "otherMethodName"
    RESULT = "result"

    method: CovidTestType = required_field()
    date_: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2021, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    otherMethodName: str = default_field()
    result: CovidTestResult = required_field()


@convertibleclass
class HealthProblemsOrDisabilityItem:
    REPORTED_BEFORE = "reportedBefore"
    SYMPTOMS_LIST = "symptomsList"
    HEALTH_ISSUE_ACTION = "healthIssueAction"
    REMOTE_CONSULTATION = "remoteConsultation"
    IN_PERSON_CONSULTATION = "inPersonConsultation"
    HOSPITALIZED_NIGHTS = "hospitalizedNights"
    IS_MEDICATIONS_PRESCRIBED = "isMedicationsPrescribed"
    MEDICATION_NAME = "medicationName"
    RECEIVE_DIAGNOSIS = "receivedDiagnosis"
    DIAGNOSIS_NAME = "diagnosisName"
    LOST_DAYS_AT_WORK_OR_EDUCATION = "lostDaysAtWorkOrEducation"
    LOST_WORK_DAYS = "lostWorkDays"
    LOST_EDUCATION_DAYS = "lostEducationDays"
    IS_HEALTH_ISSUE_DUE_TO_COVID = "isHealthIssueDueToCovid"
    TOOK_COVID_TEST = "tookCovidTest"
    NUM_COVID_TESTS_TAKEN = "numCovidTestsTaken"
    COVID_TEST_LIST = "covidTestList"
    OTHER_NEW_OR_WORSE_SYMPTOMS = "otherNewOrWorseSymptoms"

    reportedBefore: YesNoDont = required_field()
    symptomsList: list[SymptomsListItem] = required_field()
    healthIssueAction: list[HealthIssueAction] = required_field()
    remoteConsultation: int = default_field(metadata=meta(validate_range(0, 100)))
    inPersonConsultation: int = default_field(metadata=meta(validate_range(0, 100)))
    hospitalizedNights: int = default_field(metadata=meta(validate_range(1, 600)))
    isMedicationsPrescribed: bool = required_field()
    medicationName: list[str] = default_field()
    receivedDiagnosis: YesNoDont = required_field()
    diagnosisName: list[str] = default_field()
    lostDaysAtWorkOrEducation: YesNoNa = required_field()
    lostWorkDays: int = default_field(metadata=meta(validate_range(0, 600)))
    lostEducationDays: int = default_field(metadata=meta(validate_range(0, 600)))
    isHealthIssueDueToCovid: bool = required_field()
    tookCovidTest: YesNoDont = default_field()
    numCovidTestsTaken: int = default_field(metadata=meta(validate_range(1, 10)))
    covidTestList: list[CovidTestListItem] = default_field()
    otherNewOrWorseSymptoms: bool = default_field()


@convertibleclass
class HealthStatus(SkippedFieldsMixin, Primitive):
    """HealthStatus model"""

    NEW_OR_WORSE_SYMPTOMS = "newOrWorseSymptoms"
    HEALTH_PROBLEMS_OR_DISABILITIES = "healthProblemsOrDisabilityList"
    METADATA = "metadata"

    newOrWorseSymptoms: NewSymptomAction = required_field()
    healthProblemsOrDisabilityList: list[
        HealthProblemsOrDisabilityItem
    ] = default_field()
    metadata: QuestionnaireMetadata = required_field()
