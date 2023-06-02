import datetime
from enum import IntEnum

from extensions.module_result.common.enums import YesNoDont
from extensions.module_result.common.questionnaire_utils import START_DATE_IN_2020
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    utc_str_to_date,
    utc_date_to_str,
    validate_past_pregnancies_elective_termination,
    validate_past_pregnancies_miscarriage,
    validate_past_pregnancies_ectopic,
    validate_past_pregnancies_stillborn_baby,
    validate_past_pregnancies_live_birth,
    validate_pregnancy_count,
    validate_number_of_babies_multiple_birth,
    validate_pregnancy_weeks,
    validate_expected_due_date,
    validate_date_range,
)
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class PregnancyUpdate(SkippedFieldsMixin, Primitive):
    """PregnancyUpdate model"""

    class PregnancyResult(IntEnum):
        LIVE_BIRTH = 0
        MISCARRIAGE = 1
        ELECTIVE_ABORTION = 2
        STILLBIRTH = 3
        ECTOPIC = 4
        NONE = 5

    class PrenatalScreening(IntEnum):
        ULTRASOUND = 0
        BLOOD_TEST_DNA = 1
        CVS = 2
        AMNIOCENTESIS = 3
        NONE = 4

    HAS_MENSTRUAL_PERIOD = "hasMenstrualPeriod"
    LAST_MENSTRUAL_PERIOD_DATE_DAY1 = "lastMenstrualPeriodDateDay1"
    BECAME_PREGNANT = "becamePregnant"
    IS_PREGNANCY_CURRENT = "isPregnancyCurrent"
    IS_EXPECTED_DUE_DATE_AVAILABLE = "isExpectedDueDateAvailable"
    EXPECTED_DUE_DATE = "expectedDueDate"
    PREGNANCY_MORE_THAN1 = "pregnancyMoreThan1"
    BABY_COUNT = "babyCount"
    PAST_PREGNANCY_MORE_THAN_1 = "pastPregnancyMoreThan1"
    PAST_BABY_COUNT = "pastBabyCount"
    PREGNANCY_RESULT = "pregnancyResult"
    HAS_OTHER_PREGNANCY_OUTCOME = "hasOtherPregnancyOutcome"
    OTHER_PREGNANCY_RESULT = "otherPregnancyResult"
    PAST_PREGNANCY_WEEKS = "pastPregnancyWeeks"
    HAS_PAST_PREGNANCY = "hasPastPregnancy"
    PREGNANCY_TIMES = "pregnancyTimes"
    PAST_PREGNANCY_LIFE_BIRTH = "pastPregnancyLifeBirth"
    PAST_PREGNANCY_STILL_BORN = "pastPregnancyStillBorn"
    PAST_PREGNANCY_ECTOPIC = "pastPregnancyEctopic"
    PAST_PREGNANCY_MISCARRIAGE = "pastPregnancyMiscarriage"
    PAST_PREGNANCY_ELECTIVE_TERMINATION = "pastPregnancyElectiveTermination"
    HAS_VISIT_MEDICAL_PROFESSIONAL = "hasVisitMedicalProfessional"
    HIGH_RISK_CONDITION = "highRiskCondition"
    HIGH_RISK_CONDITION_ANSWERS = "highRiskConditionAnswers"
    FAMILY_HISTORY_DEFECTS = "familyHistoryDefects"
    FAMILY_HISTORY_DEFECTS_ANSWERS = "familyHistoryDefectsAnswers"
    HAS_PRENATAL_SCREENING = "hasPrenatalScreening"
    PRENATAL_SCREENING_ANSWERS = "prenatalScreeningAnswers"
    HAS_OTHER_PRENATAL_SCREENING = "hasOtherPrenatalScreening"
    OTHER_PRENATAL_SCREENING = "otherPrenatalScreening"
    HAS_SCREENING_PROBLEM = "hasScreeningProblem"
    SCREENING_PROBLEM_TEXT = "screeningProblemText"
    METADATA = "metadata"

    hasMenstrualPeriod: bool = required_field()
    lastMenstrualPeriodDateDay1: datetime.date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2020, lambda: str(datetime.date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    becamePregnant: bool = default_field()
    isPregnancyCurrent: bool = default_field()
    isExpectedDueDateAvailable: bool = default_field()
    expectedDueDate: datetime.date = default_field(
        metadata=meta(
            validator=validate_expected_due_date,
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    pregnancyMoreThan1: YesNoDont = default_field()
    babyCount: int = default_field(
        metadata=meta(validator=validate_number_of_babies_multiple_birth)
    )
    pastPregnancyMoreThan1: YesNoDont = default_field()
    pastBabyCount: int = default_field(
        metadata=meta(validator=validate_number_of_babies_multiple_birth)
    )
    pregnancyResult: list[PregnancyResult] = default_field()
    hasOtherPregnancyOutcome: bool = default_field()
    otherPregnancyResult: list[str] = default_field()
    pastPregnancyWeeks: int = default_field(
        metadata=meta(validator=validate_pregnancy_weeks)
    )
    hasPastPregnancy: YesNoDont = default_field()
    pregnancyTimes: int = default_field(
        metadata=meta(validator=validate_pregnancy_count)
    )
    pastPregnancyLifeBirth: int = default_field(
        metadata=meta(validator=validate_past_pregnancies_live_birth)
    )
    pastPregnancyStillBorn: int = default_field(
        metadata=meta(validator=validate_past_pregnancies_stillborn_baby)
    )
    pastPregnancyEctopic: int = default_field(
        metadata=meta(validator=validate_past_pregnancies_ectopic)
    )
    pastPregnancyMiscarriage: int = default_field(
        metadata=meta(validator=validate_past_pregnancies_miscarriage)
    )
    pastPregnancyElectiveTermination: int = default_field(
        metadata=meta(validator=validate_past_pregnancies_elective_termination)
    )
    hasVisitMedicalProfessional: bool = default_field()
    highRiskCondition: YesNoDont = default_field()
    highRiskConditionAnswers: list[str] = default_field()
    familyHistoryDefects: YesNoDont = default_field()
    familyHistoryDefectsAnswers: list[str] = default_field()
    hasPrenatalScreening: bool = default_field()
    prenatalScreeningAnswers: list[PrenatalScreening] = default_field()
    hasOtherPrenatalScreening: bool = default_field()
    otherPrenatalScreening: str = default_field()
    hasScreeningProblem: bool = default_field()
    screeningProblemText: str = default_field()
    metadata: QuestionnaireMetadata = required_field()
