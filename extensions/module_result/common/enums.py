from enum import IntEnum, Enum


class Regularly(IntEnum):
    STRONGLY_AGREE = 0
    AGREE = 1
    NEITHER_AGREE_DISAGREE = 2
    STRONGLY_DISAGREE = 3
    NOT_APPLICABLE = 4
    DISAGREE = 5


class YesNoDont(IntEnum):
    YES = 0
    NO = 1
    DONT_KNOW = 2

    @classmethod
    def _missing_(cls, value):
        for item in YesNoDont:
            if item.name == value:
                return item


class YesNoNa(IntEnum):
    YES = 0
    NO = 1
    NA = 2


class MedicalFertility(IntEnum):
    DONOR_EGSS = 0
    FERTILITY_MEDS = 1
    ICSI = 2
    IUI = 3
    IVF = 4
    NONE = 5


class VaccineLocation(IntEnum):
    HEALTHCARE_PROVIDER = 0
    DOCTOR_OFFICE_CLINIC = 1
    HOSPITAL = 2
    PHARMACY_DRUGSTORE = 3
    WORK = 4
    HEALTH_CLINIC_VETERANRS_FACILITY = 5
    SCHOOL_STUDENT_CLINIC = 6
    MILITARY_BASE = 7
    MOBILE_VACC_UNIT = 8
    OTHER_VACC_CENTER = 9
    AIRPORT = 10
    OTHER = 11


class PhotoVaccinationCard(IntEnum):
    PHOTO_VACC_CARD = 0
    NO_PHOTO_VACC_CARD = 1


class BabyQuantity(IntEnum):
    SINGLE_BABY = 0
    MULTIPLE_BABY = 1
    DONT_KNOW = 2


class Count(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


class PregnancyOutcome(IntEnum):
    LIVE_BIRTH = 0
    MISCARRIAGE = 1
    ELECTIVE_ABORTION = 2
    STILLBIRTH = 3
    ECTOPIC_PREG = 4
    OTHER = 5


class BabyGender(IntEnum):
    FEMALE = 0
    MALE = 1
    INTERSEX = 2


class GenderIdentity(IntEnum):
    FEMALE = 0
    MALE = 1
    NON_BINARY = 2
    OTHER = 3
    PREFER_NOTSAY = 4


class Employment(IntEnum):
    EMPLOYED = 0
    UNEMPLOYED = 1
    RETIRED = 2
    SELF_EMPLOYED = 3
    STUDENT = 4
    OTHER = 5


class SmokingStatus(IntEnum):
    NEVER = 0
    FORMER = 1
    CURRENT = 2


class SmokingStopped(IntEnum):
    YEAR_OR_LESS = 0
    ONE_TO_FIVE = 1
    OVER_FIVE = 2


class ChildBirth(IntEnum):
    VAGINAL = 0
    CAESAREAN = 1


class SymptomIntensity(IntEnum):
    MILD = 0
    MODERATE = 1
    SEVERE = 2


class NewSymptomAction(IntEnum):
    CONSULT_DOCTOR = 0
    DISABILITY_INCAPACITATION = 1
    NONE = 2


class HealthIssueAction(IntEnum):
    CONSULT_DOCTOR = 0
    VISIT_ER = 1
    HOSPITALIZED = 2
    ICU_CCU = 3


class CovidTestType(IntEnum):
    NOSE_THROAT_SWAB = 0
    SALIVA = 1
    BLOOD_FINGER_PRICK = 2
    OTHER = 3
    DONT_KNOW = 4


class CovidTestResult(IntEnum):
    POSITIVE = 0
    NEGATIVE = 1
    INCONCLUSIVE = 2
    PENDING = 3
    DONT_KNOW = 4


class CovidTestOverall(IntEnum):
    NONE_POSITIVE = 0
    ONE_POSITIVE = 1
    PENDING = 2


class CovidSymptoms(IntEnum):
    FEVER = 0
    BREATH_SHORTNESS = 1
    CHEST_PAIN = 2
    COUGH = 3
    FATIGUE_TIRED = 4
    ACHES_PAINS = 5
    HEADACHE = 6
    LOSS_OF_SMELL = 7
    SLEEP_DISTURBANCE = 8
    DIARRHOEA_VOMIT = 9


class BrandOfVaccine(IntEnum):
    MODERNA = 0
    PFIZER_BIONTECH = 1
    JANSSEN = 2
    NOVAVAX = 3
    BHARAT_BIOTECH = 4
    FBRI = 5
    GAMALEYA = 6
    COVISHIELD = 7
    SINOPHARM = 8
    SINOVAC = 9


class PlaceOfVaccination(IntEnum):
    PRIMARY_HEALTH_PROVIDER = 0
    OTHER_DOCTOR = 1
    HOSPITAL = 2
    PHARMACY_DRUGSTORE = 3
    AT_WORK = 4
    PUB_HEALTH_CLINIC_VET_ADMIN_FACILITY = 5
    SCHOOL_HEALTH_CLINIC = 6
    MILITARY_BASE = 7
    MOBILE_VAC_UNIT = 8
    OTHER_MASS_VAC_CENTRE = 9
    AIRPORT = 10
    OTHER = 11


class BeforeAfter(IntEnum):
    BEFORE = 0
    AFTER = 1


class BreastFeedingBabyIssue(IntEnum):
    DOC_OR_HOSPITAL = 0
    DISABILITY = 1
    NONE = 2


class MedicalDiagnosis(IntEnum):
    CHRONIC_RESPIRATORY = 0
    DIABETES = 1
    CEREBRO_VASCULAR = 2
    HEART_DISEASE = 3
    OTHER_CARDIO = 4
    BLEEDING_DISORDER = 5
    CHRONIC_KIDNEY = 6
    LIVER = 7
    AUTO_IMMUNE = 8
    SOLID_ORGAN_TRANSPLANT = 9
    NEURO_IMMUNE = 10
    OTHER_CONDITION = 11
    ALLERGY = 12
    DEPRESSION_ANXIETY = 13
    VIRAL_BACTERIAL = 14
    OTHER_CHRONIC = 15
    NONE = 16


class VaccineCategory(IntEnum):
    DTPA = 0
    HEPATITIS_A_or_B = 1
    HPV = 2
    MENINGITIS = 3
    PNEUMOCOCCUS = 4
    SINGLES = 5
    OTHER = 6


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Period(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class Ethnicity(Enum):
    WHITE = "WHITE"
    MIXED_OR_MULTI_ETHNIC_GROUPS = "MIXED_OR_MULTI_ETHNIC_GROUPS"
    ASIAN_OR_ASIAN_BRITISH = "ASIAN_OR_ASIAN_BRITISH"
    BLACK_OR_AFRICAN_OR_CARIBBEAN_OR_BLACK_BRITISH = "BLACK_OR_AFRICAN_OR_CARIBBEAN_OR_BLACK_BRITISH"
    OTHER_ETHNIC_GROUPS = "OTHER_ETHNIC_GROUPS"


class BloodType(Enum):
    O_POSITIVE = "O_POSITIVE"
    O_NEGATIVE = "O_NEGATIVE"
    A_POSITIVE = "A_POSITIVE"
    A_NEGATIVE = "A_NEGATIVE"
    B_POSITIVE = "B_POSITIVE"
    B_NEGATIVE = "B_NEGATIVE"
    AB_POSITIVE = "AB_POSITIVE"
    AB_NEGATIVE = "AB_NEGATIVE"
    UNKNOWN = "UNKNOWN"


class PreExistingCondition(Enum):
    CURRENT_CANCER = "CURRENT_CANCER"
    DIABETES = "DIABETES"
    HEALTH_FAILURE = "HEALTH_FAILURE"
    CHRONIC_KIDNEY_DISEASE = "CHRONIC_KIDNEY_DISEASE"
    CHRONIC_LUNG_DISEASE = "CHRONIC_LUNG_DISEASE"
    CHRONIC_LIVER_DISEASE = "CHRONIC_LIVER_DISEASE"
    CARDIOVASCULAR_DISEASE = "CARDIOVASCULAR_DISEASE"
    STROKE = "STROKE"
    HYPERTENSION = "HYPERTENSION"
    OTHER = "OTHER"
    NONE = "NONE"


class CurrentSymptom(Enum):
    DIFFICULT_BREATHING = "DIFFICULT_BREATHING"
    CHEST_TIGHTNESS = "CHEST_TIGHTNESS"
    PERSISTENT_NEW_COUGH = "PERSISTENT_NEW_COUGH"
    COUGHING_UP_PHLEGM = "COUGHING_UP_PHLEGM"
    HEADACHE = "HEADACHE"
    MYALGIA = "MYALGIA"
    FATIGUE = "FATIGUE"
    NAUSEA = "NAUSEA"
    DIARRHOEA = "DIARRHOEA"
    GI_SYMPTOMS = "GI_SYMPTOMS"
    HEMOPTYSIS = "HEMOPTYSIS"


class Covid19TestScore(Enum):
    I_WAS_TESTED_AND_DIAGNOSED_WITH_COVID_19 = "I_WAS_TESTED_AND_DIAGNOSED_WITH_COVID_19"
    I_WAS_TESTED_NEGATIVE_FOR_COVID_19 = "I_WAS_TESTED_NEGATIVE_FOR_COVID_19"
    I_WAS_TESTED_AND_AWAITING_RESULTS = "I_WAS_TESTED_AND_AWAITING_RESULTS"
    I_WAS_NOT_TESTED_FOR_COVID_19 = "I_WAS_NOT_TESTED_FOR_COVID_19"


class Covid19TestType(Enum):
    BLOOD_TEST_ANTIBODY = "BLOOD_TEST_ANTIBODY"
    SWAB_TEST_ANTIGEN = "SWAB_TEST_ANTIGEN"


class BiologicalSex(Enum):
    FEMALE = "FEMALE"
    MALE = "MALE"
    OTHER = "OTHER"
    NOT_SPECIFIED = "NOT_SPECIFIED"


class SmokeStatus(Enum):
    YES_AND_I_STILL_DO = "YES_AND_I_STILL_DO"
    YES_BUT_I_QUIT = "YES_BUT_I_QUIT"
    NO = "NO"
