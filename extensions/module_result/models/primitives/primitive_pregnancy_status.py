from datetime import date
from enum import IntEnum

from extensions.module_result.common.enums import YesNoDont
from extensions.module_result.common.questionnaire_utils import START_DATE_IN_2020
from sdk import meta, convertibleclass
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    utc_date_to_str,
    utc_str_to_date,
    not_empty,
    not_empty_list,
    validate_range,
    validate_date_range,
)
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


class MedicalFacility(IntEnum):
    DONOR_EGGS = 0
    FERTILITY_MEDS = 1
    ICSI = 2
    IUI = 3
    IVF = 4
    NONE = 5


class PreNatalScreening(IntEnum):
    ULTRASOUND = 0
    BLOOD_TEST_DNA = 1
    CVS = 2
    AMNIOCENTESIS = 3
    NONE = 4


@convertibleclass
class PregnancyStatus(SkippedFieldsMixin, Primitive):
    MENSTRUAL_PERIOD = "menstrualPeriod"
    LAST_MENSTRUAL_PERIOD_DATE = "lastMenstrualPeriodDate"
    PREGNANCY_STATUS = "pregnancyStatus"
    IS_EXPECTED_DUE_DATE_AVAILABLE = "isExpectedDueDateAvailable"
    EXPECTED_DUE_DATE = "expectedDueDate"
    PREGNANCY_MORE_THAN_1 = "pregnancyMoreThan1"
    BABY_COUNT = "babyCount"
    HAS_MEDICAL_FERTILITY_PROCEDURE = "hasMedicalFertilityProcedure"
    MEDICAL_FERTILITY_PROCEDURE_ANSWER = "medicalFertilityProcedureAnswer"
    HAS_OTHER_MEDICAL_FERTILITY_PROCEDURE = "hasOtherMedicalFertilityProcedure"
    OTHER_MEDICAL_FERTILITY_PROCEDURE_ANSWER = "otherMedicalFertilityProcedureAnswer"
    PREGNANT_BEFORE = "pregnantBefore"
    PREGNANCY_TIMES = "pregnancyTimes"
    PAST_PREGNANCY_LIVE_BIRTH = "pastPregnancyLiveBirth"
    PAST_PREGNANCY_STILL_BORN = "pastPregnancyStillBorn"
    PAST_PREGNANCY_MISCARRIAGE = "pastPregnancyMiscarriage"
    PAST_PREGNANCY_ECTOPIC = "pastPregnancyEctopic"
    PAST_PREGNANCY_ELECTIVE_TERMINATION = "pastPregnancyElectiveTermination"
    HAS_MEDICAL_PROFESSIONAL_VISIT = "hasMedicalProfessionalVisit"
    HIGH_RISK_CONDITION = "highRiskCondition"
    HIGH_RISK_CONDITION_ANSWERS = "highRiskConditionAnswers"
    FAMILY_HISTORY_DEFECTS = "familyHistoryDefects"
    FAMILY_HISTORY_DEFECTS_ANSWERS = "familyHistoryDefectsAnswers"
    HAS_PRENATAL_SCREENING = "hasPrenatalScreening"
    PRE_NATAL_SCREENING_ANSWER = "prenatalScreeningAnswer"
    HAS_OTHER_PRENATAL_SCREENING = "hasOtherPrenatalScreening"
    OTHER_PRENATAL_SCREENING = "otherPrenatalScreening"
    HAS_OTHER_SCREENING_PROBLEM = "hasOtherScreeningProblem"
    OTHER_SCREENING_PROBLEM = "otherScreeningProblem"
    METADATA = "metadata"

    menstrualPeriod: bool = required_field()
    lastMenstrualPeriodDate: date = default_field(
        metadata=meta(
            validate_date_range(START_DATE_IN_2020, lambda: str(date.today())),
            field_to_value=utc_date_to_str,
            value_to_field=utc_str_to_date,
        ),
    )
    pregnancyStatus: YesNoDont = default_field()
    isExpectedDueDateAvailable: bool = default_field()
    expectedDueDate: date = default_field(
        metadata=meta(field_to_value=utc_date_to_str, value_to_field=utc_str_to_date),
    )
    pregnancyMoreThan1: YesNoDont = default_field()
    babyCount: int = default_field(
        metadata=meta(validate_range(1, 10), value_to_field=int)
    )
    hasMedicalFertilityProcedure: bool = default_field()
    medicalFertilityProcedureAnswer: list[MedicalFacility] = default_field()
    hasOtherMedicalFertilityProcedure: bool = default_field()
    otherMedicalFertilityProcedureAnswer: str = default_field(metadata=meta(not_empty))
    pregnantBefore: YesNoDont = default_field()
    pregnancyTimes: int = default_field(
        metadata=meta(validate_range(1, 40), value_to_field=int)
    )
    pastPregnancyLiveBirth: int = default_field(
        metadata=meta(validate_range(0, 20), value_to_field=int)
    )
    pastPregnancyStillBorn: int = default_field(
        metadata=meta(validate_range(0, 20), value_to_field=int)
    )
    pastPregnancyMiscarriage: int = default_field(
        metadata=meta(validate_range(0, 40), value_to_field=int)
    )
    pastPregnancyEctopic: int = default_field(
        metadata=meta(validate_range(0, 20), value_to_field=int)
    )
    pastPregnancyElectiveTermination: int = default_field(
        metadata=meta(validate_range(0, 40), value_to_field=int)
    )
    hasMedicalProfessionalVisit: bool = default_field()
    highRiskCondition: YesNoDont = default_field()
    highRiskConditionAnswers: list[str] = default_field(metadata=meta(not_empty_list))
    familyHistoryDefects: YesNoDont = default_field()
    familyHistoryDefectsAnswers: list[str] = default_field(
        metadata=meta(not_empty_list)
    )
    hasPrenatalScreening: bool = default_field()
    prenatalScreeningAnswer: list[PreNatalScreening] = default_field()
    hasOtherPrenatalScreening: bool = default_field()
    otherPrenatalScreening: str = default_field(metadata=meta(not_empty))
    hasOtherScreeningProblem: bool = default_field()
    otherScreeningProblem: str = default_field(metadata=meta(not_empty))
    metadata: QuestionnaireMetadata = required_field()
