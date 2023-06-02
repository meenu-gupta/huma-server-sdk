from datetime import date

from extensions.module_result.common.enums import (
    YesNoDont,
    CovidSymptoms,
    MedicalDiagnosis,
    HealthIssueAction,
    CovidTestType,
    CovidTestOverall,
)
from extensions.module_result.common.questionnaire_utils import START_DATE_IN_2019
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
class CancerTypeItem:
    NAME = "name"
    IS_TAKING_MEDICATION = "isTakingMedication"
    METASTATIC = "metastatic"

    name: str = required_field()
    isTakingMedication: bool = required_field()
    metastatic: YesNoDont = required_field()


@convertibleclass
class MedicalConditionsItem:
    CONDITION_NAME = "conditionName"
    IS_TAKING_MEDICATION = "isTakingMedication"

    conditionName: str = required_field()
    isTakingMedication: bool = required_field()


@convertibleclass
class OtherCovidSymptomsItem:
    NAME = "name"
    INTENSITY = "intensity"
    PERSIST_POST_INFECTION = "persistPostInfection"

    name: str = required_field()
    intensity: int = required_field(metadata=meta(validate_range(0, 10)))
    persistPostInfection: YesNoDont = required_field()


@convertibleclass
class CovidSymptomsItem:
    NAME = "name"
    INTENSITY = "intensity"
    PERSIST_POST_INFECTION = "persistPostInfection"

    name: CovidSymptoms = required_field()
    intensity: int = required_field(metadata=meta(validate_range(0, 10)))
    persistPostInfection: YesNoDont = required_field()


@convertibleclass
class MedicalHistory(SkippedFieldsMixin, Primitive):
    CANCER_TYPE = "cancerType"
    MEDICAL_DIAGNOSIS = "medicalDiagnosis"
    MEDICAL_CONDITION = "medicalConditions"
    TAKING_IMMUNO_SUPPRESSANTS = "takingImmunoSuppressants"
    IMMUNO_SUPPRESSANTS_MEDICATION_LIST = "immunoSuppressantMedicationList"
    IS_COVID_INFECTED_IN_PAST = "isCovidInfectedInPast"
    COVID_INFECTED_DATE = "covidInfectedDate"
    IS_COVID_TOLD_BY_DOCTOR = "isCovidToldByDoctor"
    COVID_TOLD_BY_DOCTOR_DATE = "covidToldByDoctorDate"
    TAKEN_COVID_TEST = "takenCovidTest"
    COVID_TEST_RESULT = "covidTestResult"
    COVID_TEST_DATE = "covidTestDate"
    COVID_TEST_METHOD = "covidTestMethod"
    COVID_TEST_OTHER = "covidTestOther"
    COVID_SYMPTOMS = "covidSymptoms"
    OTHER_COVID_SYMPTOMS = "otherCovidSymptoms"
    COVID_SYMPTOMS_ACTION = "covidSymptomAction"
    METADATA = "metadata"
    HAD_COVID_SYMPTOMS = "hadCovidSymptoms"
    HAD_OTHER_COVID_SYMPTOMS = "hadOtherCovidSymptoms"
    IS_DIAGNOSED_WITH_CANCER = "isDiagnosedWithCancer"

    cancerType: list[CancerTypeItem] = default_field()
    medicalDiagnosis: list[MedicalDiagnosis] = required_field()
    medicalConditions: list[MedicalConditionsItem] = default_field()
    takingImmunoSuppressants: YesNoDont = required_field()
    immunoSuppressantMedicationList: list[str] = default_field()
    isCovidInfectedInPast: bool = required_field()
    covidInfectedDate: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2019, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    isCovidToldByDoctor: bool = required_field()
    covidToldByDoctorDate: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2019, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    takenCovidTest: YesNoDont = required_field()
    covidTestResult: CovidTestOverall = default_field()
    covidTestDate: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2019, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    covidTestMethod: CovidTestType = default_field()
    covidTestOther: str = default_field()
    covidSymptoms: list[CovidSymptomsItem] = default_field()
    otherCovidSymptoms: list[OtherCovidSymptomsItem] = default_field()
    covidSymptomAction: list[HealthIssueAction] = default_field()
    metadata: QuestionnaireMetadata = required_field()
    hadCovidSymptoms: bool = default_field()
    hadOtherCovidSymptoms: bool = default_field()
    isDiagnosedWithCancer: bool = required_field(default=False)
