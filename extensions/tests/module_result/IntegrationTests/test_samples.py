from datetime import datetime

from dateutil.relativedelta import relativedelta

from extensions.common.s3object import FlatBufferS3Object
from extensions.module_result.common.enums import (
    SymptomIntensity,
    CovidTestType,
    CovidTestResult,
    Employment,
    GenderIdentity,
    SmokingStatus,
    SmokingStopped,
    BabyQuantity,
    BabyGender,
    ChildBirth,
    VaccineCategory,
    MedicalDiagnosis,
    NewSymptomAction,
    HealthIssueAction,
    BrandOfVaccine,
    PlaceOfVaccination,
    Regularly,
    BeforeAfter,
    YesNoDont,
    VaccineLocation,
)
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Weight,
    PeakFlow,
    PregnancyFollowUp,
    HealthStatus,
    BackgroundInformation,
    AdditionalQoL,
    FeverAndPainDrugs,
    PregnancyStatus,
    PostVaccination,
    InfantFollowUp,
    ChildrenItem,
    VaccinationDetails,
    BreastFeedingUpdateBabyDetails,
    BreastFeedingUpdate,
    BreastFeedingStatus,
    PregnancyUpdate,
    MedicalHistory,
    AZGroupKeyActionTrigger,
    AZFurtherPregnancyKeyActionTrigger,
    CurrentGroupCategory,
    GroupCategory,
    AZScreeningQuestionnaire,
    PROMISGlobalHealth,
    Questionnaire,
    QuestionnaireAnswer,
    Primitive,
    SF36,
    VaccineListItem,
    OtherVaccine,
    PreNatalScreening,
    MedicalFacility,
    HealthProblemsOrDisabilityItem,
    SymptomsListItem,
    CovidTestListItem,
    ECGReading,
    BabyInfo,
    BodyMeasurement,
    Symptom,
    ComplexSymptomValue,
)
from extensions.module_result.models.primitives.cvd_risk_score import (
    AlcoholIntake,
    WalkingPace,
    OverallHealth,
    ExistingCondition,
    ExistingSymptom,
    CurrentMedication,
    FamilyHeartDisease,
)
from extensions.module_result.models.primitives.primitive_oxford_hip import (
    OxfordHipScore,
    HipData,
    HipAffected,
)
from extensions.module_result.models.primitives.primitive_oxford_knee import (
    OxfordKneeScore,
    LegAffected,
    LegData,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionAnswerFormat,
    QuestionAnswerSelectionCriteria,
    QuestionnaireAnswerMediaType,
    QuestionnaireAnswerMediaFile,
)
from extensions.module_result.models.primitives.primitive_step import Step
from extensions.module_result.modules import NorfolkQuestionnaireModule
from extensions.module_result.modules import SF36QuestionnaireModule
from extensions.module_result.modules.eq5d_5l import EQ5D5LModule
from extensions.module_result.modules.fjs_hip_score import FJSHipScoreModule
from extensions.module_result.modules.fjs_knee_score import FJSKneeScoreModule
from extensions.module_result.modules import IKDCModule
from extensions.module_result.modules.oacs import OACSModule
from extensions.module_result.modules.oars import OARSModule
from sdk.common.utils.validators import utc_str_field_to_val, utc_date_to_str

VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"


def now_str():
    return utc_str_field_to_val(datetime.utcnow())


def common_fields():
    return {
        "deploymentId": VALID_DEPLOYMENT_ID,
        "version": 0,
        "deviceName": "iOS",
        "isAggregated": False,
        "startDateTime": now_str(),
    }


def sample_diabetes_distress_score_data() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "answers": [
            {
                QuestionnaireAnswer.QUESTION: "Feeling overwhelmed by the demands of living with diabetes.",
                QuestionnaireAnswer.QUESTION_ID: "screening_question_1",
                QuestionnaireAnswer.ANSWER_TEXT: "A serious problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that I am often failing with my diabetes routine.",
                QuestionnaireAnswer.QUESTION_ID: "screening_question_2_flow1",
                QuestionnaireAnswer.ANSWER_TEXT: "A very serious problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that diabetes is taking up too much of my mental and physical energy every day.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_1",
                QuestionnaireAnswer.ANSWER_TEXT: "Somewhat serious problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that my doctor doesn’t know enough about diabetes and diabetes care.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_2",
                QuestionnaireAnswer.ANSWER_TEXT: "A moderate problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling angry, scared, and/or depressed when I think about living with diabetes.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_3",
                QuestionnaireAnswer.ANSWER_TEXT: "A slight problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that my doctor doesn’t give me clear enough directions on how to manage my diabetes.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_4",
                QuestionnaireAnswer.ANSWER_TEXT: "Not a problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that I am not testing my blood sugars frequently enough.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_5",
                QuestionnaireAnswer.ANSWER_TEXT: "A very serious problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that I am often failing with my diabetes regimen.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_6",
                QuestionnaireAnswer.ANSWER_TEXT: "A serious problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that friends or family are not supportive enough of my self-care efforts (e.g., planning activities that conflict with my schedule, encouraging me to eat the “wrong” foods).",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_7",
                QuestionnaireAnswer.ANSWER_TEXT: "A moderate problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that diabetes controls my life.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_8",
                QuestionnaireAnswer.ANSWER_TEXT: "A slight problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that my doctor doesn’t take my concerns seriously enough.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_9",
                QuestionnaireAnswer.ANSWER_TEXT: "A serious problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Not feeling confident in my day-to-day ability to manage diabetes.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_10",
                QuestionnaireAnswer.ANSWER_TEXT: "Somewhat serious problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that I will end up with serious long-term complications, no matter what I do.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_11",
                QuestionnaireAnswer.ANSWER_TEXT: "Not a problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that I am not sticking closely enough to a good meal plan.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_12",
                QuestionnaireAnswer.ANSWER_TEXT: "Somewhat serious problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that friends or family don’t appreciate how difficult living with diabetes can be.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_13",
                QuestionnaireAnswer.ANSWER_TEXT: "A serious problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling overwhelmed by the demands of living with diabetes.?",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_14",
                QuestionnaireAnswer.ANSWER_TEXT: "Not a problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that I don’t have a doctor who I can see regularly about my diabetes.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_15",
                QuestionnaireAnswer.ANSWER_TEXT: "A very serious problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Not feeling motivated to keep up my diabetes self-management.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_16",
                QuestionnaireAnswer.ANSWER_TEXT: "A serious problem",
            },
            {
                QuestionnaireAnswer.QUESTION: "Feeling that friends or family don’t give me the emotional support that I would like.",
                QuestionnaireAnswer.QUESTION_ID: "regular_question_17",
                QuestionnaireAnswer.ANSWER_TEXT: "A very serious problem",
            },
        ],
        "moduleName": "Diabetes Distress Score",
        "moduleId": "DiabetesDistressScore",
        "questionnaireId": "5f7b2408f59b327c0ef5a84d",
        "questionnaireName": "Diabetes Distress Score",
    }


def sample_fjs_hip_score_data() -> dict:
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        "answers": [
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint in bed at night?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_bed",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint when you are sitting on a chair for more than one hour?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_chair",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint when you are walking for more than 15 minutes?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_walking",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint when you are taking a bath/shower?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_bath",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint when you are traveling in a car?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_traveling",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint when you are climbing stairs?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_climbing",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint when you are walking on uneven ground?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_walking_uneven_ground",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint when you are standing up from a low-sitting position?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_standing",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint when you are standing for long periods of time?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_standing_long_time",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint when you are doing housework or gardening?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_housework_gardening",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint when you are taking a walk/hiking?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_hiking",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your hip joint when you are doing your favorite sport?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_hip_sport",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
        ],
        Questionnaire.QUESTIONNAIRE_ID: "fjs_hip_module",
        ModuleConfig.MODULE_NAME: "FJS Hip Score",
        Primitive.MODULE_ID: FJSHipScoreModule.moduleId,
        Questionnaire.QUESTIONNAIRE_NAME: "FJS Hip Score",
        Primitive.MODULE_CONFIG_ID: "5f15af1967af6dcbc05e2780",
    }


def sample_fjs_knee_score_data() -> dict:
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        "answers": [
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint in bed at night?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_bed",
                QuestionnaireAnswer.ANSWER_TEXT: "Sometimes",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint when you are sitting on a chair for more than one hour?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_chair",
                QuestionnaireAnswer.ANSWER_TEXT: "Almost never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint when you are walking for more than 15 minutes?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_walking",
                QuestionnaireAnswer.ANSWER_TEXT: "Sometimes",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint when you are taking a bath/shower?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_bath",
                QuestionnaireAnswer.ANSWER_TEXT: "Sometimes",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint when you are traveling in a car?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_traveling",
                QuestionnaireAnswer.ANSWER_TEXT: "Mostly",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint when you are climbing stairs?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_climbing",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint when you are walking on uneven ground?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_walking_uneven_ground",
                QuestionnaireAnswer.ANSWER_TEXT: "Almost never",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint when you are standing up from a low-sitting position?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_standing",
                QuestionnaireAnswer.ANSWER_TEXT: "Seldom",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint when you are standing for long periods of time?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_standing_long_time",
                QuestionnaireAnswer.ANSWER_TEXT: "Sometimes",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint when you are doing housework or gardening?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_housework_gardening",
                QuestionnaireAnswer.ANSWER_TEXT: "Mostly",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint when you are taking a walk/hiking?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_hiking",
                QuestionnaireAnswer.ANSWER_TEXT: "Seldom",
            },
            {
                QuestionnaireAnswer.QUESTION: "Are you aware of your knee joint when you are doing your favorite sport?",
                QuestionnaireAnswer.QUESTION_ID: "fjs_knee_sport",
                QuestionnaireAnswer.ANSWER_TEXT: "Never",
            },
        ],
        Questionnaire.QUESTIONNAIRE_ID: "fjs_knee_module",
        ModuleConfig.MODULE_NAME: "FJS Knee Score",
        Primitive.MODULE_ID: FJSKneeScoreModule.moduleId,
        Questionnaire.QUESTIONNAIRE_NAME: "FJS Knee Score",
        Primitive.MODULE_CONFIG_ID: "5f15af1967af6dcbc05e2755",
    }


def sample_medication_result() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "answers": [
            {
                QuestionnaireAnswer.ANSWER_TEXT: "29",
                QuestionnaireAnswer.QUESTION_ID: "7c50c7d5-6f4e-4c0b-aeaf-c266eafd056e",
                QuestionnaireAnswer.QUESTION: "give us a number",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "I feel bad",
                QuestionnaireAnswer.QUESTION_ID: "6ac67dc1-f155-4dd7-b4df-2868b12235d3",
                QuestionnaireAnswer.QUESTION: "How are you feeling",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Hey",
                QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c7",
                QuestionnaireAnswer.QUESTION: "Choose one",
            },
        ],
        "questionnaireId": "749e6294-034e-4366-a9c9-83027d5c0fe3",
        "questionnaireName": "MedicationTracker",
    }


def sample_questionnaire(
    questionnaire_id: str = "749e6294-034e-4366-a9c9-83027d5c0fe4",
) -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "answers": [
            {
                QuestionnaireAnswer.ANSWER_TEXT: "29",
                QuestionnaireAnswer.QUESTION_ID: "7c50c7d5-6f4e-4c0b-aeaf-c266eafd056e",
                QuestionnaireAnswer.QUESTION: "give us a number",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "I feel bad",
                QuestionnaireAnswer.QUESTION_ID: "6ac67dc1-f155-4dd7-b4df-2868b12235d3",
                QuestionnaireAnswer.QUESTION: "How are you feeling",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Hey",
                QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c7",
                QuestionnaireAnswer.QUESTION: "Choose one",
            },
        ],
        "questionnaireId": questionnaire_id,
        "questionnaireName": "Questionnaire",
    }


def sample_questionnaire_with_reverse_and_max_score() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "answers": [
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Nearly every day",
                QuestionnaireAnswer.QUESTION_ID: "d571d295-9da6-4583-98dc-db92126a4f99",
                QuestionnaireAnswer.QUESTION: "Feeling nervous, anxious or on edge?",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "More than half the days",
                QuestionnaireAnswer.QUESTION_ID: "12ed5202-e636-4929-8d31-6ecdec107c99",
                QuestionnaireAnswer.QUESTION: "Not being able to stop or control worrying?",
            },
        ],
        "questionnaireId": "eeb23d05-d23f-4eb7-ad57-52d70a8edd99",
        "questionnaireName": "Questionnaire",
    }


def sample_oxford_hip_score() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "answers": [
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Nearly every day",
                QuestionnaireAnswer.QUESTION_ID: "d571d295-9da6-4583-98dc-db92126a4f34",
                QuestionnaireAnswer.QUESTION: "Feeling nervous, anxious or on edge?",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "More than half the days",
                QuestionnaireAnswer.QUESTION_ID: "12ed5202-e636-4929-8d31-6ecdec107cee",
                QuestionnaireAnswer.QUESTION: "Not being able to stop or control worrying?",
            },
        ],
        "questionnaireId": "eeb23d05-d23f-4eb7-ad57-52d70a8edd77",
        "questionnaireName": "OxfordHipScore",
    }


def sample_pam_questionnaire_result() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "answers": [
            {
                QuestionnaireAnswer.QUESTION: "PA1",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA2",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA3",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA4",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA5",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA6",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA7",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA8",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA9",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA10",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA11",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA12",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
            {
                QuestionnaireAnswer.QUESTION: "PA13",
                QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            },
        ],
        "questionnaireId": "d7c92a9e-ca3b-4f73-824e-3b1ac3b5141d",
        "questionnaireName": "Questionnaire",
    }


def sample_questionnaire_with_recall_text(
    questionnaire_id: str = "749e6294-034e-4366-a9c9-83027d5c0fe4",
) -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "answers": [
            {
                QuestionnaireAnswer.ANSWER_TEXT: "29",
                QuestionnaireAnswer.QUESTION_ID: "7c50c7d5-6f4e-4c0b-aeaf-c266eafd056e",
                QuestionnaireAnswer.QUESTION: "give us a number",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c7",
                QuestionnaireAnswer.QUESTION: "Ok, why have you chosen @{}?",
                QuestionnaireAnswer.RECALLED_TEXT: ["recalled text one"],
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "no difference if this field is here or not",
                QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c7",
                QuestionnaireAnswer.QUESTION: "Ok, why have you chosen @{}?",
                QuestionnaireAnswer.RECALLED_TEXT: [
                    "recalled text one",
                    "recalled text two",
                ],
            },
        ],
        "questionnaireId": questionnaire_id,
        "questionnaireName": "Questionnaire",
    }


def sample_sensor_capture() -> dict:
    return {
        **common_fields(),
        "type": "SensorCapture",
        "s3Object": {"bucket": "bucket", "key": "key", "region": "eu"},
        "sanityCheck": True,
        "value": 60.0,
        "measurementLocation": "CHEST",
        "sensorDataTypes": ["ACCELEROMETER", "GYROSCOPE"],
    }


def sample_weight(value=100):
    return {
        **common_fields(),
        "type": "Weight",
        "value": value,
    }


def sample_blood_glucose(value=15.0):
    return {
        **common_fields(),
        "type": "BloodGlucose",
        "value": value,
    }


def sample_bg_thresholds():
    return [
        {
            "name": "Test",
            "severity": 1,
            "type": "VALUE",
            "color": "green",
            "fieldName": "value",
            "resultsCount": 1,
            "enabled": True,
            "thresholdRange": [{"minValue": 2.0, "maxValue": 5.0}],
        },
        {
            "name": "Test2",
            "severity": 2,
            "type": "VALUE",
            "color": "amber",
            "fieldName": "value",
            "resultsCount": 1,
            "enabled": True,
            "thresholdRange": [
                {"minValue": 5.1, "maxValue": 11.0},
            ],
        },
        {
            "name": "Test3",
            "severity": 3,
            "type": "VALUE",
            "color": "red",
            "fieldName": "value",
            "resultsCount": 1,
            "enabled": True,
            "thresholdRange": [{"maxValue": 1.9}],
        },
        {
            "name": "Test3",
            "severity": 3,
            "type": "VALUE",
            "color": "red",
            "fieldName": "value",
            "resultsCount": 1,
            "enabled": True,
            "thresholdRange": [{"minValue": 11.1}],
        },
    ]


def sample_heart_rate(value=100, include_extra_fields=False):
    base = {
        **common_fields(),
        "type": "HeartRate",
        "value": value,
    }
    return (
        base
        if not include_extra_fields
        else {
            **base,
            **{
                "variabilityAVNN": 99,
                "variabilitySDNN": 100,
                "variabilityRMSSD": 100,
                "variabilityPNN50": 100.1,
                "variabilityprcLF": 100.1,
                "confidence": 10,
                "goodIBI": 9,
                "rawDataObject": {
                    "bucket": "bucket",
                    "key": "key",
                    "region": "eu",
                },
                "classification": "Regular",
            },
        }
    )


def sample_high_frequency_heart_rate_multiple_values(value=0):
    base = {
        **common_fields(),
        "type": "HighFrequencyHeartRate",
        "value": value,
    }
    return {
        **base,
        **{
            "startDateTime": "2019-06-30T00:00:00Z",
            "endDateTime": "2019-06-30T02:00:00Z",
            "dataType": "MULTIPLE_VALUE",
            "rawDataObject": {"bucket": "bucket", "key": "key", "region": "eu"},
            "value": 0,
            "multipleValues": [
                {
                    "id": "5b5279d1e303d394db6ea0f8",
                    "p": {"0": 56.56, "15": 56.56, "30": 56.58, "45": 57.02},
                    "d": "2019-06-30T00:00:00Z",
                },
                {
                    "id": "5b5279d1e303d394db6ea134",
                    "p": {"0": 69.47, "15": 69.47, "30": 68.46, "45": 69.45},
                    "d": "2019-06-30T01:00:00Z",
                },
            ],
        },
    }


def sample_high_frequency_heart_rate_multiple_values_second(value=0):
    base = {
        **common_fields(),
        "type": "HighFrequencyHeartRate",
        "value": value,
    }
    return {
        **base,
        **{
            "startDateTime": "2019-07-30T00:00:00Z",
            "endDateTime": "2019-07-30T02:00:00Z",
            "dataType": "MULTIPLE_VALUE",
            "rawDataObject": {"bucket": "bucket", "key": "key", "region": "eu"},
            "value": 0,
            "multipleValues": [
                {
                    "id": "5b5279d1e303d394db6ea0f8",
                    "p": {"0": 56.56, "15": 56.56, "30": 56.58, "45": 57.02},
                    "d": "2019-07-30T00:00:00Z",
                },
                {
                    "id": "5b5279d1e303d394db6ea134",
                    "p": {"0": 69.47, "15": 69.47, "30": 68.46, "45": 69.45},
                    "d": "2019-07-30T01:00:00Z",
                },
            ],
        },
    }


def sample_high_frequency_heart_rate_ppg_type():
    base = {
        **common_fields(),
        "type": "HighFrequencyHeartRate",
    }
    return {
        **base,
        **{
            "startDateTime": "2019-06-30T00:00:00Z",
            "endDateTime": "2019-06-30T02:00:00Z",
            "dataType": "PPG_VALUE",
            "rawDataObject": {"bucket": "bucket", "key": "key", "region": "eu"},
            "value": 90,
        },
    }


def sample_high_frequency_heart_rate_single_value():
    base = {**common_fields(), "type": "HighFrequencyHeartRate"}
    return {
        **base,
        **{
            "startDateTime": "2019-06-30T00:00:00Z",
            "endDateTime": "2019-06-30T02:00:00Z",
            "dataType": "SINGLE_VALUE",
            "rawDataObject": {"bucket": "bucket", "key": "key", "region": "eu"},
            "value": 90,
        },
    }


def sample_eq5d_questionnaire_result_with_multiple_arabic_answers() -> dict:
    sample_eq5d_questionnaire = sample_eq5d_questionnaire_result()

    valid_answers = [
        "مشاكل في العین",
        "مشاكل في الكلى",
        "مشاكل في الدورة الدمویة",
        "مضاعفات أخرى",
        "لا شيء",
    ]
    arabic_multiple_answer = ",".join(valid_answers[:3])
    sample_eq5d_questionnaire["answers"][0][
        QuestionnaireAnswer.ANSWER_TEXT
    ] = arabic_multiple_answer
    return sample_eq5d_questionnaire


def sample_eq5d_questionnaire_result_deprecated() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "answers": [
            {
                QuestionnaireAnswer.QUESTION_ID: "b037104f-8c1d-42a7-bb94-851206b8f057",
                QuestionnaireAnswer.QUESTION: "Your mobility TODAY",
                QuestionnaireAnswer.ANSWER_TEXT: "I have no problems in walking about",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "ace68441-6a3a-4ccd-9a26-8c37dc3273d9",
                QuestionnaireAnswer.QUESTION: "Your self-care TODAY",
                QuestionnaireAnswer.ANSWER_TEXT: "I have moderate problems washing or dressing myself",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "dc5632b4-2ce7-4b72-b187-e4f8f777a94a",
                QuestionnaireAnswer.QUESTION: "Your usual activities TODAY",
                QuestionnaireAnswer.ANSWER_TEXT: "I have severe problems doing my usual activities",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "647a6dc7-2289-4988-8451-c791c72b924f",
                QuestionnaireAnswer.QUESTION: "Your pain/discomfort TODAY",
                QuestionnaireAnswer.ANSWER_TEXT: "I have extreme pain or discomfort",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "0cc66b89-108e-44d2-966a-e3a7be63bd63",
                QuestionnaireAnswer.QUESTION: "Your anxiety/depression TODAY",
                QuestionnaireAnswer.ANSWER_TEXT: "I'm not anxious or pressed",
            },
        ],
        "questionnaireId": "b13403cb-f24e-4721-b362-9929bf0421ff",
        "questionnaireName": "Questionnaire",
    }


def sample_eq5d_questionnaire_result() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        Questionnaire.MODULE_ID: EQ5D5LModule.moduleId,
        Questionnaire.MODULE_CONFIG_ID: "5d386cc6ff885918d96edb4a",
        Questionnaire.QUESTIONNAIRE_NAME: EQ5D5LModule.moduleId,
        "answers": [
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_mobility",
                QuestionnaireAnswer.QUESTION: "Your mobility TODAY",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.ANSWER_TEXT: "hu_eq5d5l_mob_label1",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_selfcare",
                QuestionnaireAnswer.QUESTION: "Your self-care TODAY",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.ANSWER_TEXT: "hu_eq5d5l_selfcare_label3",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_usualactivity",
                QuestionnaireAnswer.QUESTION: "Your usual activities TODAY",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.ANSWER_TEXT: "hu_eq5d5l_usualactivity_label4",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_paindiscomfort",
                QuestionnaireAnswer.QUESTION: "Your pain/discomfort TODAY",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.ANSWER_TEXT: "hu_eq5d5l_paindis_label5",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_anxiety",
                QuestionnaireAnswer.QUESTION: "Your anxiety/depression TODAY",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.ANSWER_TEXT: "hu_eq5d5l_anxiety_label1",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_scale",
                QuestionnaireAnswer.QUESTION: "Please tap or drag the scale to indicate how your health is TODAY",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.SCALE.value,
                QuestionnaireAnswer.VALUE: 50,
            },
        ],
        "questionnaireId": "b13403cb-f24e-4721-b362-9929bf0421ff",
        "questionnaireName": "Questionnaire",
    }


def sample_german_eq5d_questionnaire_result() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        Questionnaire.MODULE_ID: EQ5D5LModule.moduleId,
        Questionnaire.MODULE_CONFIG_ID: "5d386cc6ff885918d96edb4a",
        Questionnaire.QUESTIONNAIRE_NAME: EQ5D5LModule.moduleId,
        "answers": [
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_mobility",
                QuestionnaireAnswer.QUESTION: "<b>Beweglichkeit / Mobilität HEUTE</b>",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.ANSWER_TEXT: "Ich habe keine Probleme herumzugehen ",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_selfcare",
                QuestionnaireAnswer.QUESTION: "<b>Für sich selbst sorgen - HEUTE</b>",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.ANSWER_TEXT: "Ich habe mäßige Probleme, mich selbst zu waschen oder anzuziehen ",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_usualactivity",
                QuestionnaireAnswer.QUESTION: "<b>Alltägliche Tätigkeiten HEUTE</b>",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.ANSWER_TEXT: "Ich habe große Probleme, meinen alltäglichen Tätigkeiten nachzugehen ",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_paindiscomfort",
                QuestionnaireAnswer.QUESTION: "<b>Schmerzen / körperliche Beschwerden HEUTE</b>",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.ANSWER_TEXT: "Ich habe extreme Schmerzen oder Beschwerden",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_anxiety",
                QuestionnaireAnswer.QUESTION: "<b>Angst / Niedergeschlagenheit HEUTE</b>",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.ANSWER_TEXT: "Ich bin nicht ängstlich oder deprimiert",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_scale",
                QuestionnaireAnswer.QUESTION: "Bitte tippen Sie den Punkt auf der Skala an, der Ihre Gesundheit HEUTE am besten beschreibt.",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.SCALE.value,
                QuestionnaireAnswer.VALUE: 50,
            },
        ],
        "questionnaireId": "b13403cb-f24e-4721-b362-9929bf0421ff",
        "questionnaireName": "Questionnaire",
    }


def sample_respiratory_rate(value=26):
    return {**common_fields(), "type": "RespiratoryRate", "value": value}


def sample_bmi_data() -> dict:
    return {
        "type": Weight.__name__,
        "deviceName": "iOS",
        "deploymentId": VALID_DEPLOYMENT_ID,
        "startDateTime": now_str(),
        "value": 80,
    }


def sample_peak_flow_data() -> dict:
    return {
        **common_fields(),
        "type": PeakFlow.__name__,
        "value": 400,
    }


def sample_group_information() -> dict:
    return {
        **common_fields(),
        "type": AZGroupKeyActionTrigger.__name__,
        AZGroupKeyActionTrigger.FIRST_VACCINE_DATE: "2021-03-30",
        AZGroupKeyActionTrigger.GROUP_CATEGORY: GroupCategory.BREAST_FEEDING,
        AZGroupKeyActionTrigger.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                    QuestionnaireAnswer.QUESTION: "Which of the following group is most applicable to you?",
                    QuestionnaireAnswer.ANSWER_TEXT: "I am pregnant",
                }
            ]
        },
    }


def sample_leg_data(value: int = 2) -> dict:
    non_answers_fields = [LegData.LEG_AFFECTED, LegData.SCORE]
    leg_data_keys = LegData().__annotations__.keys()
    return {k: value for k in leg_data_keys if k not in non_answers_fields}


def sample_oxford_only_one_knee_score(affected_leg: int, leg_value: int = 2) -> dict:
    return {
        **common_fields(),
        "type": OxfordKneeScore.__name__,
        OxfordKneeScore.LEG_AFFECTED: affected_leg,
        OxfordKneeScore.LEGS_DATA: [sample_leg_data(leg_value)],
    }


def sample_oxford_both_knee_score() -> dict:
    return {
        **common_fields(),
        "type": OxfordKneeScore.__name__,
        OxfordKneeScore.LEG_AFFECTED: LegAffected.BOTH.value,
        OxfordKneeScore.LEGS_DATA: [sample_leg_data(), sample_leg_data(3)],
    }


def sample_hip_data(value: int = 2) -> dict:
    non_answers_fields = [HipData.HIP_AFFECTED, HipData.SCORE]
    hip_data_keys = HipData().__annotations__.keys()
    return {k: value for k in hip_data_keys if k not in non_answers_fields}


def sample_oxford_only_one_hip_score(affected_hip: int, hip_value: int = 2) -> dict:
    return {
        **common_fields(),
        "type": OxfordHipScore.__name__,
        OxfordHipScore.HIP_AFFECTED: affected_hip,
        OxfordHipScore.HIPS_DATA: [sample_hip_data(hip_value)],
    }


def sample_oxford_both_hip_score() -> dict:
    return {
        **common_fields(),
        "type": OxfordHipScore.__name__,
        OxfordHipScore.HIP_AFFECTED: HipAffected.BOTH.value,
        OxfordHipScore.HIPS_DATA: [sample_hip_data(), sample_hip_data(3)],
    }


def sample_further_information() -> dict:
    return {
        **common_fields(),
        "type": AZFurtherPregnancyKeyActionTrigger.__name__,
        AZFurtherPregnancyKeyActionTrigger.CURRENT_GROUP_CATEGORY: CurrentGroupCategory.PREGNANT,
        AZFurtherPregnancyKeyActionTrigger.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                    QuestionnaireAnswer.QUESTION: "Which of the following group is most applicable to you?",
                    QuestionnaireAnswer.ANSWER_TEXT: "I am pregnant",
                }
            ]
        },
    }


def sample_breathlessness() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "answers": [
            {
                QuestionnaireAnswer.ANSWER_TEXT: "2",
                QuestionnaireAnswer.QUESTION_ID: "7c50c7d5-6f4e-4c0b-aeaf-c266eafdt587",
                QuestionnaireAnswer.QUESTION: "give us a number",
            }
        ],
        "questionnaireId": "5f7b2408f59b327c0ef5a847",
        "questionnaireName": "Breathlessness",
    }


def sample_koos_answers(answer_text: str = "hu_koos_option_moderate") -> list:
    answers = []
    # we need a lot of questions in order to pass validation and calculate scores
    question_ids = [
        "koos_pain_flat_surface",
        "koos_pain_activities",
        "koos_pain_straightening",
        "koos_pain_bending",
        "koos_pain_experience",
        "koos_symptom_wakening",
        "koos_symptom_sitting",
        "koos_symptom_knee_hangup",
        "koos_symptom_knee_straighten",
        "koos_function_standing",
        "koos_function_pickup_object",
        "koos_function_flat_surface",
        "koos_function_shopping",
        "koos_function_stockings",
        "koos_function_rising_bed",
        "koos_function_descending_stairs",
        "koos_function_ascending_stairs",
        "koos_function_rising",
        "koos_sports_squatting",
        "koos_sports_running",
        "koos_sports_jumping",
        "koos_quality_often_aware",
        "koos_quality_modified_lifestyle",
    ]
    for question_id in question_ids:
        answers.append(
            {
                QuestionnaireAnswer.ANSWER_TEXT: answer_text,
                QuestionnaireAnswer.QUESTION_ID: question_id,
                QuestionnaireAnswer.QUESTION: f"{question_id}: Some tricky, question",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.SINGLE.value,
                QuestionnaireAnswer.SELECTED_CHOICES: [answer_text],
                QuestionnaireAnswer.CHOICES: [],
            }
        )
    return answers


def sample_koos_and_womac_data() -> dict:
    data = {
        **common_fields(),
        "type": "Questionnaire",
        Questionnaire.QUESTIONNAIRE_ID: "611dffd20d4e78155ae591e8",
        Questionnaire.ANSWERS: sample_koos_answers(),
        Questionnaire.MODULE_ID: "KOOS",
        Questionnaire.QUESTIONNAIRE_NAME: "KOOS",
        Questionnaire.MODULE_CONFIG_ID: "611cf7585b09ef8f119be014",
        Questionnaire.SKIPPED: [
            {
                QuestionnaireAnswer.QUESTION_ID: "koos_function_stockings",
                QuestionnaireAnswer.QUESTION: "koos_function_stockings: Some tricky, question",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.SINGLE.value,
                QuestionnaireAnswer.SELECTED_CHOICES: ["111"],
                QuestionnaireAnswer.CHOICES: [],
            }
        ],
    }
    return data


def sample_koos_and_womac_data_with_not_enough_answers() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "answers": [
            {
                QuestionnaireAnswer.ANSWER_TEXT: "hu_koos_option_moderate",
                QuestionnaireAnswer.QUESTION_ID: "koos_quality_modified_lifestyle",
                QuestionnaireAnswer.QUESTION: "Do you have swelling in your knee?",
            }
        ],
        "questionnaireId": "611dffd20d4e78155ae591e8",
        "moduleName": "KOOS",
        "moduleId": "KOOS",
        "questionnaireName": "KOOS",
        "moduleConfigId": "611cf7585b09ef8f119be014",
    }


def sample_health_status() -> dict:
    return {
        **common_fields(),
        "type": HealthStatus.__name__,
        HealthStatus.NEW_OR_WORSE_SYMPTOMS: NewSymptomAction.CONSULT_DOCTOR,
        HealthStatus.HEALTH_PROBLEMS_OR_DISABILITIES: [
            {
                HealthProblemsOrDisabilityItem.REPORTED_BEFORE: YesNoDont.NO,
                HealthProblemsOrDisabilityItem.SYMPTOMS_LIST: [
                    {
                        SymptomsListItem.NAME: "Headache",
                        SymptomsListItem.INTENSITY: SymptomIntensity.SEVERE,
                        SymptomsListItem.START_DATE: "2021-02-12T00:00:00Z",
                        SymptomsListItem.IS_RESOLVED: False,
                        SymptomsListItem.END_DATE: "2021-03-20T00:00:00Z",
                    }
                ],
                HealthProblemsOrDisabilityItem.HEALTH_ISSUE_ACTION: [
                    HealthIssueAction.CONSULT_DOCTOR,
                    HealthIssueAction.HOSPITALIZED,
                ],
                HealthProblemsOrDisabilityItem.IS_MEDICATIONS_PRESCRIBED: True,
                HealthProblemsOrDisabilityItem.RECEIVE_DIAGNOSIS: YesNoDont.YES,
                HealthProblemsOrDisabilityItem.LOST_DAYS_AT_WORK_OR_EDUCATION: 2,
                HealthProblemsOrDisabilityItem.IS_HEALTH_ISSUE_DUE_TO_COVID: True,
                HealthProblemsOrDisabilityItem.TOOK_COVID_TEST: YesNoDont.YES,
                HealthProblemsOrDisabilityItem.OTHER_NEW_OR_WORSE_SYMPTOMS: True,
                HealthProblemsOrDisabilityItem.COVID_TEST_LIST: [
                    {
                        CovidTestListItem.METHOD: CovidTestType.NOSE_THROAT_SWAB,
                        CovidTestListItem.DATE: "2021-01-30T00:00:00Z",
                        CovidTestListItem.RESULT: CovidTestResult.PENDING,
                    }
                ],
            }
        ],
        HealthStatus.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                    QuestionnaireAnswer.QUESTION: " How intense was your headache?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Severe",
                }
            ]
        },
    }


def sample_background_information() -> dict:
    return {
        **common_fields(),
        "type": BackgroundInformation.__name__,
        BackgroundInformation.AGE: 19,
        BackgroundInformation.SEX_AT_BIRTH: BabyGender.MALE,
        BackgroundInformation.GENDER_IDENTITY: GenderIdentity.MALE,
        BackgroundInformation.GENDER_OTHER: "Transgender",
        BackgroundInformation.RESIDENCY_COUNTRY: "Germany",
        BackgroundInformation.BIRTH_COUNTRY: "Germany",
        BackgroundInformation.WEIGHT: 200,
        BackgroundInformation.HEIGHT: 120,
        BackgroundInformation.EMPLOYMENT: Employment.STUDENT,
        BackgroundInformation.IS_HEALTHCARE_WORKER: False,
        BackgroundInformation.SMOKING_STATUS: SmokingStatus.FORMER,
        BackgroundInformation.SMOKING_STOPPED: SmokingStopped.ONE_TO_FIVE,
        BackgroundInformation.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
                    QuestionnaireAnswer.QUESTION: "How old are you?",
                    QuestionnaireAnswer.ANSWER_TEXT: "19",
                },
            ]
        },
    }


def sample_breastfeeding_update() -> dict:
    stop_date = utc_date_to_str(datetime.utcnow() - relativedelta(months=3))
    return {
        **common_fields(),
        "type": BreastFeedingUpdate.__name__,
        BreastFeedingUpdate.IS_BREASTFEEDING_NOW: True,
        BreastFeedingUpdate.STOP_DATE: stop_date,
        BreastFeedingUpdate.NOW_OR_WORSE_SYMPTOM: [
            NewSymptomAction.DISABILITY_INCAPACITATION
        ],
        BreastFeedingUpdate.BREASTFEEDING_BABY_DETAILS: [
            {
                BreastFeedingUpdateBabyDetails.HEALTH_ISSUE: [],
                BreastFeedingUpdateBabyDetails.HEALTH_ISSUE_ACTION: [
                    HealthIssueAction.CONSULT_DOCTOR,
                    HealthIssueAction.VISIT_ER,
                ],
                BreastFeedingUpdateBabyDetails.HAS_RECEIVED_DIAGNOSIS: True,
                BreastFeedingUpdateBabyDetails.DIAGNOSIS_LIST: [],
            }
        ],
        BreastFeedingUpdate.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "7c50c7d5-6f4e-4c0b-aeaf-c266eafdt587",
                    QuestionnaireAnswer.QUESTION: "Are you currently breastfeeding?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                }
            ]
        },
    }


def sample_breastfeeding_status() -> dict:
    return {
        **common_fields(),
        "type": BreastFeedingStatus.__name__,
        BreastFeedingStatus.IS_BREASTFEEDING_CURRENTLY: False,
        BreastFeedingStatus.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
                    QuestionnaireAnswer.QUESTION: "Are you currently breastfeeding?",
                    QuestionnaireAnswer.ANSWER_TEXT: "No",
                },
            ]
        },
    }


def sample_medical_history() -> dict:
    return {
        **common_fields(),
        "type": MedicalHistory.__name__,
        MedicalHistory.MEDICAL_DIAGNOSIS: [MedicalDiagnosis.DIABETES],
        MedicalHistory.TAKING_IMMUNO_SUPPRESSANTS: YesNoDont.YES,
        MedicalHistory.IMMUNO_SUPPRESSANTS_MEDICATION_LIST: ["Test"],
        MedicalHistory.IS_COVID_INFECTED_IN_PAST: True,
        MedicalHistory.IS_COVID_TOLD_BY_DOCTOR: False,
        MedicalHistory.TAKEN_COVID_TEST: YesNoDont.NO,
        MedicalHistory.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "7c50c7d5-6f4e-4c0b-aeaf-c266eafdt587",
                    QuestionnaireAnswer.QUESTION: "Please specify which type of cancer?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Colorectal Cancer",
                }
            ]
        },
        MedicalHistory.IS_DIAGNOSED_WITH_CANCER: False,
    }


def sample_daily_check_in() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "answers": [
            {
                QuestionnaireAnswer.ANSWER_TEXT: "1",
                QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
                QuestionnaireAnswer.QUESTION: "Are you feeling better than yesterday?",
            }
        ],
        "questionnaireId": "5f7b2408f59b327c0ef5a842",
        "questionnaireName": "DailyCheckIn",
    }


def sample_post_vaccination() -> dict:
    return {
        **common_fields(),
        "type": PostVaccination.__name__,
        PostVaccination.SECOND_COVID_VACCINATION_DOSE: "2019-06-30",
        PostVaccination.IS_SECOND_DOSE_AZ: True,
        PostVaccination.SECOND_DOSE_BRAND: BrandOfVaccine.NOVAVAX,
        PostVaccination.BATCH_NUMBER_VACCINE: "ABV4678",
        PostVaccination.IS_SAME_PLACE_VACCINE_2_AS_1: True,
        PostVaccination.VACCINATION_PLACE: PlaceOfVaccination.AIRPORT,
        PostVaccination.VACCINATION_PLACE_OTHER: "HOME",
        PostVaccination.VACCINATION_PLACE_LOCATION: "Test",
        PostVaccination.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                    QuestionnaireAnswer.QUESTION: "Please provide the date of your second COVID-19 vaccination dose.",
                    QuestionnaireAnswer.ANSWER_TEXT: "2019-06-30",
                }
            ]
        },
    }


def sample_gad_7() -> dict:
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        Questionnaire.ANSWERS: [
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Not at all",
                QuestionnaireAnswer.QUESTION_ID: "d571d295-9da6-4583-98dc-db92126a4f34",
                QuestionnaireAnswer.QUESTION: "Feeling nervous, anxious or on edge?",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Nearly every day",
                QuestionnaireAnswer.QUESTION_ID: "12ed5202-e636-4929-8d31-6ecdec107cee",
                QuestionnaireAnswer.QUESTION: "Not being able to stop or control worrying?",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Not at all",
                QuestionnaireAnswer.QUESTION_ID: "181c7bf0-e765-45e9-894b-805ff65c529a",
                QuestionnaireAnswer.QUESTION: "Worrying too much about different things?",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Not at all",
                QuestionnaireAnswer.QUESTION_ID: "359501cb-60cf-4307-b3e5-2aaa8d1949ef",
                QuestionnaireAnswer.QUESTION: "Trouble relaxing?",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Nearly every day",
                QuestionnaireAnswer.QUESTION_ID: "1739c17d-6bca-440d-a21a-565209700bfd",
                QuestionnaireAnswer.QUESTION: "Being so restless that it is hard to sit still?",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Not at all",
                QuestionnaireAnswer.QUESTION_ID: "707fbe5e-96bc-4b60-acd9-aeeaa9a1270d",
                QuestionnaireAnswer.QUESTION: "Becoming easily annoyed or irritable?",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Not at all",
                QuestionnaireAnswer.QUESTION_ID: "f1065a9d-2bb9-4f68-b143-9685a1bd80b1",
                QuestionnaireAnswer.QUESTION: "Feeling afraid as if something awful might happen?",
            },
        ],
        Questionnaire.QUESTIONNAIRE_ID: "eeb23d05-d23f-4eb7-ad57-52d70a8edd29",
        Questionnaire.QUESTIONNAIRE_NAME: "Mental health: GAD-7",
        Questionnaire.MODULE_ID: "GeneralAnxietyDisorder",
    }


def sample_medication() -> dict:
    return {
        **common_fields(),
        "type": "Medication",
    }


def sample_ecg() -> dict:
    from extensions.tests.module_result.IntegrationTests.module_result_tests import (
        ECG_SAMPLE_FILE,
    )

    return {
        **common_fields(),
        "type": "ECGHealthKit",
        "value": 1,
        "ecgReading": {
            ECGReading.AVERAGE_HEART_RATE: 1850.4,
            ECGReading.DATA_POINTS: {
                FlatBufferS3Object.BUCKET: "integrationtests",
                FlatBufferS3Object.KEY: ECG_SAMPLE_FILE,
                FlatBufferS3Object.REGION: "eu",
                FlatBufferS3Object.FBS_VERSION: 1,
            },
        },
    }


def sample_pregnancy_status() -> dict:
    return {
        **common_fields(),
        "type": PregnancyStatus.__name__,
        PregnancyStatus.MENSTRUAL_PERIOD: True,
        PregnancyStatus.LAST_MENSTRUAL_PERIOD_DATE: "2020-06-30",
        PregnancyStatus.PREGNANCY_STATUS: YesNoDont.DONT_KNOW,
        PregnancyStatus.IS_EXPECTED_DUE_DATE_AVAILABLE: True,
        PregnancyStatus.EXPECTED_DUE_DATE: "2019-06-30",
        PregnancyStatus.PREGNANCY_MORE_THAN_1: YesNoDont.YES,
        PregnancyStatus.BABY_COUNT: 2,
        PregnancyStatus.HAS_MEDICAL_FERTILITY_PROCEDURE: True,
        PregnancyStatus.MEDICAL_FERTILITY_PROCEDURE_ANSWER: [
            MedicalFacility.DONOR_EGGS
        ],
        PregnancyStatus.HAS_OTHER_PRENATAL_SCREENING: True,
        PregnancyStatus.OTHER_MEDICAL_FERTILITY_PROCEDURE_ANSWER: "Test",
        PregnancyStatus.PREGNANT_BEFORE: YesNoDont.YES,
        PregnancyStatus.PAST_PREGNANCY_LIVE_BIRTH: 1,
        PregnancyStatus.PAST_PREGNANCY_STILL_BORN: 1,
        PregnancyStatus.PAST_PREGNANCY_MISCARRIAGE: 1,
        PregnancyStatus.PAST_PREGNANCY_ECTOPIC: 1,
        PregnancyStatus.PAST_PREGNANCY_ELECTIVE_TERMINATION: 1,
        PregnancyStatus.HAS_MEDICAL_PROFESSIONAL_VISIT: True,
        PregnancyStatus.HIGH_RISK_CONDITION: YesNoDont.DONT_KNOW,
        PregnancyStatus.HIGH_RISK_CONDITION_ANSWERS: ["Test"],
        PregnancyStatus.FAMILY_HISTORY_DEFECTS: YesNoDont.YES,
        PregnancyStatus.FAMILY_HISTORY_DEFECTS_ANSWERS: ["Test"],
        PregnancyStatus.HAS_PRENATAL_SCREENING: True,
        PregnancyStatus.PRE_NATAL_SCREENING_ANSWER: [PreNatalScreening.ULTRASOUND],
        PregnancyStatus.OTHER_PRENATAL_SCREENING: "Test",
        PregnancyStatus.HAS_OTHER_SCREENING_PROBLEM: True,
        PregnancyStatus.OTHER_SCREENING_PROBLEM: "Test",
        PregnancyStatus.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                    QuestionnaireAnswer.QUESTION: "Are you currently pregnant?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                }
            ]
        },
    }


def sample_fever_and_pain_drugs() -> dict:
    return {
        **common_fields(),
        "type": "FeverAndPainDrugs",
        FeverAndPainDrugs.HAS_ANTI_FEVER_PAIN_DRUGS: True,
        FeverAndPainDrugs.MED_STARTED_BEFORE_AFTER: BeforeAfter.BEFORE,
        FeverAndPainDrugs.DAYS_BEFORE_VAC_MEDICATION: 4,
        FeverAndPainDrugs.DAYS_AFTER_VAC_MEDICATION: 5,
        FeverAndPainDrugs.IS_UNDER_MEDICATION: True,
        FeverAndPainDrugs.DAYS_COUNT_MEDICATION: 12,
        FeverAndPainDrugs.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "cf323797-9909-4500-933e-16854d2b0d77",
                    QuestionnaireAnswer.QUESTION: "In order to prevent/treat symptoms that could be related to vaccination, did you take any anti-fever or pain-relieving medication such as paracetamol (e.g. Doliprane or Dafalgan) or ibuprofen (e.g. Advil or Nurofen) within five days of your dose of COVID-19 vaccine?",
                    QuestionnaireAnswer.ANSWER_TEXT: "true",
                }
            ]
        },
    }


def sample_additional_qol() -> dict:
    return {
        **common_fields(),
        "type": "AdditionalQoL",
        AdditionalQoL.VIEW_FAMILY: Regularly.STRONGLY_DISAGREE,
        AdditionalQoL.CONTACT_PROFESSIONALS: Regularly.AGREE,
        AdditionalQoL.CONTRIBUTE_ACTIVITIES: Regularly.NEITHER_AGREE_DISAGREE,
        AdditionalQoL.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "30cad609-cd6a-418d-a1de-6eacfa3a2d9d",
                    QuestionnaireAnswer.QUESTION: "I am able to see my friends and family more in person",
                    QuestionnaireAnswer.ANSWER_TEXT: "AGREE",
                }
            ]
        },
    }


def sample_infant_follow_up() -> dict:
    return {
        **common_fields(),
        "type": InfantFollowUp.__name__,
        InfantFollowUp.IS_COV_PREG_LIVE_BIRTH: True,
        InfantFollowUp.CHILDREN: [
            {
                ChildrenItem.ISSUES: ["ADHD", "Cerebral Palsy"],
                ChildrenItem.HAS_CHILD_DEVELOP_ISSUES: True,
            }
        ],
        InfantFollowUp.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "fbeeb07a-64c4-409d-aac7-c929674022a1",
                    QuestionnaireAnswer.QUESTION: "Are you aware or has a medical doctor informed you of any developmental issues with your first child from this pregnancy?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                }
            ]
        },
    }


def sample_vaccination_details() -> dict:
    return {
        **common_fields(),
        "type": VaccinationDetails.__name__,
        VaccinationDetails.VACCINATED_PLACE: VaccineLocation.HOSPITAL,
        VaccinationDetails.VACCINATION_LOCATION: "NHS",
        VaccinationDetails.VACCINATION_CITY: "London",
        VaccinationDetails.BATCH_NUMBER: "ABV3922",
        VaccinationDetails.IS_SECOND_DOSE_VACC: YesNoDont.YES,
        VaccinationDetails.IS_SEASON_FLU_VAC: False,
        VaccinationDetails.IS_OTHER_SPECIFIED_VACC: True,
        VaccinationDetails.IS_ALLERGIC_REACTION_VACC: YesNoDont.DONT_KNOW,
        VaccinationDetails.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "032db29f-363c-418f-b626-2fa21adcc557",
                    QuestionnaireAnswer.QUESTION: "Where were you vaccinated?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Hospital",
                },
                {
                    QuestionnaireAnswer.QUESTION_ID: "1d8efcfc-02c8-4153-95c3-f9bdb32499e0",
                    QuestionnaireAnswer.QUESTION: "Please specify where",
                    QuestionnaireAnswer.ANSWER_TEXT: "NHS",
                },
                {
                    QuestionnaireAnswer.QUESTION_ID: "3ce7cf65-f3d6-4bd0-8e67-fd9c98b636fd",
                    QuestionnaireAnswer.QUESTION: "Please specify the city/town.",
                    QuestionnaireAnswer.ANSWER_TEXT: "London",
                },
            ]
        },
    }


def sample_pregnancy_update() -> dict:
    return {
        **common_fields(),
        "type": "PregnancyUpdate",
        PregnancyUpdate.HAS_MENSTRUAL_PERIOD: True,
        PregnancyUpdate.LAST_MENSTRUAL_PERIOD_DATE_DAY1: "2021-01-01T00:00:00Z",
        PregnancyUpdate.BECAME_PREGNANT: False,
        PregnancyUpdate.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "a285d625-54d1-421f-ba5e-d9748690c461",
                    QuestionnaireAnswer.QUESTION: "Have you had your menstrual period in the last year?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                },
                {
                    QuestionnaireAnswer.QUESTION_ID: "de8a8e98-81a7-42be-a33f-0b8f0393ada1",
                    QuestionnaireAnswer.QUESTION: "What was the first day of your last menstrual period date? ",
                    QuestionnaireAnswer.ANSWER_TEXT: "2021-01-01T00:00:00Z",
                },
                {
                    QuestionnaireAnswer.QUESTION_ID: "0f473b35-1dc9-40de-af16-17eaa4f4ff7f",
                    QuestionnaireAnswer.QUESTION: "Are you currently pregnant?",
                    QuestionnaireAnswer.ANSWER_TEXT: "No",
                },
            ]
        },
    }


def sample_other_vaccine() -> dict:
    return {
        **common_fields(),
        "type": OtherVaccine.__name__,
        OtherVaccine.HAS_FLU_VACCINE: True,
        OtherVaccine.FLU_VACCINE_DATE: "2021-03-30",
        OtherVaccine.HAS_OTHER_VACCINE: True,
        OtherVaccine.VACCINE_CATEGORY: [
            VaccineCategory.HPV,
            VaccineCategory.MENINGITIS,
        ],
        OtherVaccine.VACCINE_LIST: [
            {
                VaccineListItem.NAME: "Sinopharm",
                VaccineListItem.VACCINATED_DATE: "2021-03-30",
            }
        ],
        OtherVaccine.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
                    QuestionnaireAnswer.QUESTION: "Have you received the seasonal flu vaccine since the last time we asked?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                },
            ]
        },
    }


def sample_pregnancy_follow_up() -> dict:
    return {
        **common_fields(),
        "type": PregnancyFollowUp.__name__,
        PregnancyFollowUp.PREGNANCY_MEDICATION: True,
        PregnancyFollowUp.OVER_COUNTER_PREGNANCY_MEDICATIONS: True,
        PregnancyFollowUp.OVER_COUNTER_MEDICATIONS: [],
        PregnancyFollowUp.BABY_COUNT: BabyQuantity.MULTIPLE_BABY,
        PregnancyFollowUp.CURRENT_BABY_COUNT: 2,
        PregnancyFollowUp.BABY_INFO: [
            {
                BabyInfo.PREGNANCY_FOR_BABY: 1,
                BabyInfo.DATE_DELIVERY: "2021-01-30",
                BabyInfo.PREGNANCY_DURATION: 34,
                BabyInfo.SPECIFIED_OUTCOME: [],
                BabyInfo.BABY_GENDER: BabyGender.MALE,
                BabyInfo.METHOD_DELIVERY: ChildBirth.VAGINAL,
                BabyInfo.IS_BREAST_FEEDING_BABY: True,
                BabyInfo.IS_CURRENTLY_BREASTFEEDING_BABY: True,
                BabyInfo.BREASTFEED_LONG_TERM: 12,
                BabyInfo.IS_BABY_NO_LIQUID: True,
                BabyInfo.IS_BABY_ISSUES: 1,
                BabyInfo.SPECIFIED_ISSUES: [],
            }
        ],
        PregnancyFollowUp.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                    QuestionnaireAnswer.QUESTION: "What was the method of delivery?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Caesarean section",
                }
            ]
        },
    }


def sample_az_screening():
    return {
        **common_fields(),
        "type": AZScreeningQuestionnaire.__name__,
        AZScreeningQuestionnaire.HAS_RECEIVED_COVID_VAC_IN_PAST_4_WEEKS: True,
        AZScreeningQuestionnaire.IS_AZ_VAC_FIRST_DOSE: True,
        AZScreeningQuestionnaire.IS_18_Y_OLD_DURING_VAC: True,
        AZScreeningQuestionnaire.METADATA: {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION: "Are you 18 years old?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                },
            ]
        },
    }


def sample_promis_global_health():
    return {
        **common_fields(),
        "type": PROMISGlobalHealth.__name__,
        PROMISGlobalHealth.GLOBAL_01: 2,
        PROMISGlobalHealth.GLOBAL_02: 3,
        PROMISGlobalHealth.GLOBAL_03: 2,
        PROMISGlobalHealth.GLOBAL_04: 3,
        PROMISGlobalHealth.GLOBAL_05: 2,
        PROMISGlobalHealth.GLOBAL_06: 3,
        PROMISGlobalHealth.GLOBAL_07_RC: 5,
        PROMISGlobalHealth.GLOBAL_08_R: 2,
        PROMISGlobalHealth.GLOBAL_09_R: 3,
        PROMISGlobalHealth.GLOBAL_10_R: 2,
        PROMISGlobalHealth.METADATA: {QuestionnaireMetadata.ANSWERS: []},
    }


def sample_surgery_details_answers():
    return [
        {
            QuestionnaireAnswer.ANSWER_TEXT: "2021-03-30",
            QuestionnaireAnswer.QUESTION_ID: "discharge q",
            QuestionnaireAnswer.QUESTION: "What was the hospital discharge date?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Partial hip replacement",
            QuestionnaireAnswer.QUESTION_ID: "partial hip repl q",
            QuestionnaireAnswer.QUESTION: "Operation type",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "OTHER",
            QuestionnaireAnswer.QUESTION_ID: "surg approach",
            QuestionnaireAnswer.QUESTION: "What surgical approach",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "other approach",
            QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c1",
            QuestionnaireAnswer.QUESTION: "Other value of surgical approach",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "YES_RI_HIP_NAVIGATION",
            QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c2",
            QuestionnaireAnswer.QUESTION: "What technology assistance",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "other assistance",
            QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c3",
            QuestionnaireAnswer.QUESTION: "Other value of technology assistance",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "CEMENTED",
            QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c4",
            QuestionnaireAnswer.QUESTION: "What fixation",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "SL_MIA_CEMENTLESS",
            QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c5",
            QuestionnaireAnswer.QUESTION: "What stem",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "OTHER_CEMENTED",
            QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c6",
            QuestionnaireAnswer.QUESTION: "What shell",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "other shell",
            QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c7",
            QuestionnaireAnswer.QUESTION: "Other value of shell",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "OTHER",
            QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c8",
            QuestionnaireAnswer.QUESTION: "What bearing",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "other bearing",
            QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c9",
            QuestionnaireAnswer.QUESTION: "Other value of bearing",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "OSTEOARTHRITIS",
            QuestionnaireAnswer.QUESTION_ID: "ed499bd4-bbfb-45c7-bb5d-b2075c7c65c0",
            QuestionnaireAnswer.QUESTION: "What indication",
        },
    ]


def sample_surgery_details() -> dict:
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        Questionnaire.ANSWERS: sample_surgery_details_answers(),
        Questionnaire.QUESTIONNAIRE_ID: "eeb23d05-d23f-4eb7-ad57-52d70a8edd30",
        Questionnaire.QUESTIONNAIRE_NAME: "Surgery details",
    }


def sample_kccq_answers() -> list[dict]:
    answers = []
    question_ids_and_answers = [
        ("kccq_physical_limitation_q1a", "hu_kccq_phylimit_q1option1"),
        ("kccq_physical_limitation_q1b", "hu_kccq_phylimit_q1option1"),
        ("kccq_physical_limitation_q1c", "hu_kccq_phylimit_q1option1"),
        ("kccq_physical_limitation_q1d", "hu_kccq_phylimit_q1option1"),
        ("kccq_physical_limitation_q1e", "hu_kccq_phylimit_q1option1"),
        ("kccq_physical_limitation_q1f", "hu_kccq_phylimit_q1option1"),
        ("kccq_symptom_stability_q2", "hu_kccq_symstab_q2option1"),
        ("kccq_symptom_frequency_q3", "hu_kccq_symfreq_q3option1"),
        ("kccq_symptom_burden_q4", "hu_kccq_extremely_bothersome"),
        ("kccq_symptom_frequency_q5", "hu_kccq_all_time"),
        ("kccq_symptom_burden_q6", "hu_kccq_extremely_bothersome"),
        ("kccq_symptom_frequency_q7", "hu_kccq_all_time"),
        ("kccq_symptom_burden_q8", "hu_kccq_extremely_bothersome"),
        ("kccq_symptom_frequency_q9", "hu_kccq_symfreq_q9option1"),
        ("kccq_self_efficacy_q10", "hu_kccq_selfeff_q10option1"),
        ("kccq_self_efficacy_q11", "hu_kccq_selfeff_q11option1"),
        ("kccq_quality_of_life_q12", "hu_kccq_qol_q12option1"),
        ("kccq_quality_of_life_q13", "hu_kccq_qol_q13option1"),
        ("kccq_quality_of_life_q14", "hu_kccq_qol_q14option1"),
        ("kccq_social_limitation_q15a", "hu_kccq_soclimit_option1"),
        ("kccq_social_limitation_q15b", "hu_kccq_soclimit_option1"),
        ("kccq_social_limitation_q15c", "hu_kccq_soclimit_option1"),
        ("kccq_social_limitation_q15d", "hu_kccq_soclimit_option1"),
    ]
    for question_id, answer in question_ids_and_answers:
        answers.append(
            {
                QuestionnaireAnswer.ANSWER_TEXT: answer,
                QuestionnaireAnswer.QUESTION_ID: question_id,
                QuestionnaireAnswer.QUESTION: f"{question_id}: Dressing yourself",
            }
        )

    return answers


def sample_kccq_all_zero_weight_anwsers() -> dict:
    answers = []
    question_ids_and_answers = [
        ("kccq_physical_limitation_q1a", "hu_kccq_phylimit_q1option6"),
        ("kccq_physical_limitation_q1b", "hu_kccq_phylimit_q1option6"),
        ("kccq_physical_limitation_q1c", "hu_kccq_phylimit_q1option6"),
        ("kccq_physical_limitation_q1d", "hu_kccq_phylimit_q1option6"),
        ("kccq_physical_limitation_q1e", "hu_kccq_phylimit_q1option6"),
        ("kccq_physical_limitation_q1f", "hu_kccq_phylimit_q1option6"),
        ("kccq_symptom_stability_q2", "hu_kccq_symstab_q2option1"),
        ("kccq_symptom_frequency_q3", "hu_kccq_symfreq_q3option1"),
        ("kccq_symptom_burden_q4", "hu_kccq_extremely_bothersome"),
        ("kccq_symptom_frequency_q5", "hu_kccq_all_time"),
        ("kccq_symptom_burden_q6", "hu_kccq_extremely_bothersome"),
        ("kccq_symptom_frequency_q7", "hu_kccq_all_time"),
        ("kccq_symptom_burden_q8", "hu_kccq_extremely_bothersome"),
        ("kccq_symptom_frequency_q9", "hu_kccq_symfreq_q9option1"),
        ("kccq_self_efficacy_q10", "hu_kccq_selfeff_q10option1"),
        ("kccq_self_efficacy_q11", "hu_kccq_selfeff_q11option1"),
        ("kccq_quality_of_life_q12", "hu_kccq_qol_q12option1"),
        ("kccq_quality_of_life_q13", "hu_kccq_qol_q13option1"),
        ("kccq_quality_of_life_q14", "hu_kccq_qol_q14option1"),
        ("kccq_social_limitation_q15a", "hu_kccq_soclimit_option6"),
        ("kccq_social_limitation_q15b", "hu_kccq_soclimit_option6"),
        ("kccq_social_limitation_q15c", "hu_kccq_soclimit_option6"),
        ("kccq_social_limitation_q15d", "hu_kccq_soclimit_option6"),
    ]
    for question_id, answer in question_ids_and_answers:
        answers.append(
            {
                QuestionnaireAnswer.ANSWER_TEXT: answer,
                QuestionnaireAnswer.QUESTION_ID: question_id,
                QuestionnaireAnswer.QUESTION: "Dressing yourself",
            }
        )
    return {
        **common_fields(),
        "type": "Questionnaire",
        "questionnaireId": "611dffd20d4e78155ae591ef",
        "answers": answers,
        "moduleName": "KCCQ",
        "moduleId": "KCCQ",
        "questionnaireName": "KCCQ",
        "moduleConfigId": "611cf7585b09ef8f119be015",
    }


def sample_kccq_data() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        "questionnaireId": "611dffd20d4e78155ae591ef",
        "answers": sample_kccq_answers(),
        "moduleName": "KCCQ",
        "moduleId": "KCCQ",
        "questionnaireName": "KCCQ",
        "moduleConfigId": "611cf7585b09ef8f119be015",
    }


def sample_kccq_data_missing_answers() -> dict:
    answers = sample_kccq_answers()
    return {
        **common_fields(),
        "type": "Questionnaire",
        "questionnaireId": "611dffd20d4e78155ae591ef",
        "answers": answers[:6] + answers[7:],
        "moduleName": "KCCQ",
        "moduleId": "KCCQ",
        "questionnaireName": "KCCQ",
        "moduleConfigId": "611cf7585b09ef8f119be015",
    }


def sample_sf36_answers() -> list[dict]:
    answers = []
    yes_limited_a_lot = "Yes, limited a lot"
    yes = "Yes"
    not_at_all = "Not at all"
    all_of_the_time = "All of the time"
    definitely_true = "Definitely true"
    question_ids = [
        ("sf36_general_health_q1", "Excellent"),
        ("sf36_general_health_q2", "Much better now than one year ago"),
        ("sf36_limitation_activities_q3", yes_limited_a_lot),
        ("sf36_limitation_activities_q4", yes_limited_a_lot),
        ("sf36_limitation_activities_q5", yes_limited_a_lot),
        ("sf36_limitation_activities_q6", yes_limited_a_lot),
        ("sf36_limitation_activities_q7", yes_limited_a_lot),
        ("sf36_limitation_activities_q8", yes_limited_a_lot),
        ("sf36_limitation_activities_q9", yes_limited_a_lot),
        ("sf36_limitation_activities_q10", yes_limited_a_lot),
        ("sf36_limitation_activities_q11", yes_limited_a_lot),
        ("sf36_limitation_activities_q12", yes_limited_a_lot),
        ("sf36_physical_health_problems_q13", yes),
        ("sf36_physical_health_problems_q14", "No"),
        ("sf36_physical_health_problems_q15", yes),
        ("sf36_physical_health_problems_q16", yes),
        ("sf36_emotional_health_problems_q17", yes),
        ("sf36_emotional_health_problems_q18", yes),
        ("sf36_emotional_health_problems_q19", yes),
        ("sf36_social_activities_q20", not_at_all),
        ("sf36_pain_q21", "Very mild"),
        ("sf36_pain_q22", not_at_all),
        ("sf36_energy_fatigue_q23", all_of_the_time),
        ("sf36_emotional_well_being_q24", all_of_the_time),
        ("sf36_emotional_well_being_q25", all_of_the_time),
        ("sf36_emotional_well_being_q26", all_of_the_time),
        ("sf36_energy_fatigue_q27", all_of_the_time),
        ("sf36_emotional_well_being_q28", all_of_the_time),
        ("sf36_energy_fatigue_q29", all_of_the_time),
        ("sf36_emotional_well_being_q30", all_of_the_time),
        ("sf36_energy_fatigue_q31", all_of_the_time),
        ("sf36_social_activities_q32", all_of_the_time),
        ("sf36_general_health_q33", definitely_true),
        ("sf36_general_health_q34", definitely_true),
        ("sf36_general_health_q35", definitely_true),
        ("sf36_general_health_q36", definitely_true),
    ]
    for question_id, answer in question_ids:
        answers.append(
            {
                QuestionnaireAnswer.ANSWER_TEXT: answer,
                QuestionnaireAnswer.QUESTION_ID: question_id,
                QuestionnaireAnswer.QUESTION: f"{question_id}: Did you feel full of pep?",
            }
        )

    return answers


def sample_sf36_data() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        Questionnaire.QUESTIONNAIRE_ID: "611dffd20d4e78155ae591ef",
        Questionnaire.ANSWERS: sample_sf36_answers(),
        ModuleConfig.MODULE_NAME: "SF36",
        SF36.MODULE_ID: SF36QuestionnaireModule.moduleId,
        Questionnaire.QUESTIONNAIRE_NAME: "SF36",
        SF36.MODULE_CONFIG_ID: "613718cfef76b07f0317df17",
    }


def sample_sf36_missing_data() -> dict:
    return {
        **common_fields(),
        "type": "Questionnaire",
        Questionnaire.QUESTIONNAIRE_ID: "611dffd20d4e78155ae591ef",
        Questionnaire.ANSWERS: sample_sf36_answers()[3:],
        ModuleConfig.MODULE_NAME: "SF36",
        SF36.MODULE_ID: SF36QuestionnaireModule.moduleId,
        Questionnaire.QUESTIONNAIRE_NAME: "SF36",
        SF36.MODULE_CONFIG_ID: "613718cfef76b07f0317df17",
    }


def sample_norfolk_answers() -> list[dict]:
    answers = []
    YES = "Yes"
    LEFT = "Left"
    RIGHT = "Right"
    FEET_LEGS = "Feet,Legs"
    NONE = "None"
    MILD = "Mild problem"
    SEVERE = "Severe problem"
    NOT_A_PROBLEM = "Not a problem"
    MODERATE = "Moderate problem"
    VERY_MILD = "Very mild problem"
    NOT_AT_ALL = "Not at all"
    EXCELLENT = "Excellent"
    ABOUT_SAME = "About the same"
    MODERATELY = "Moderately"

    question_ids = [
        ("hu_norfolk_generic_q1", YES),
        ("hu_norfolk_generic_q2", YES),
        ("hu_norfolk_generic_q3", YES),
        ("hu_norfolk_generic_q4", ""),
        ("hu_norfolk_generic_q5", ""),
        ("hu_norfolk_generic_q6", YES),
        ("hu_norfolk_generic_q7", LEFT),
        ("hu_norfolk_generic_q8", RIGHT),
        ("hu_norfolk_generic_q9", YES),
        ("hu_norfolk_generic_q11", YES),
        ("hu_norfolk_generic_q12", YES),
        ("hu_norfolk_generic_q13", YES),
        ("hu_norfolk_generic_q14", YES),
        ("hu_norfolk_generic_q15", YES),
        ("hu_norfolk_symptom_q18", FEET_LEGS),
        ("hu_norfolk_symptom_q19", FEET_LEGS),
        ("hu_norfolk_symptom_q20", FEET_LEGS),
        ("hu_norfolk_symptom_q21", FEET_LEGS),
        ("hu_norfolk_symptom_q22", FEET_LEGS),
        ("hu_norfolk_symptom_q23", f"{FEET_LEGS},{NONE}"),
        ("hu_norfolk_symptom_q24", NONE),
        ("hu_norfolk_aodl_q25", MILD),
        ("hu_norfolk_aodl_q26", MILD),
        ("hu_norfolk_aodl_q27", MILD),
        ("hu_norfolk_aodl_q28", SEVERE),
        ("hu_norfolk_aodl_q29", SEVERE),
        ("hu_norfolk_aodl_q30", SEVERE),
        ("hu_norfolk_aodl_q31", SEVERE),
        ("hu_norfolk_aodl_q32", SEVERE),
        ("hu_norfolk_aodl_q33", NOT_A_PROBLEM),
        ("hu_norfolk_aodl_q34", NOT_A_PROBLEM),
        ("hu_norfolk_aodl_q35", NOT_A_PROBLEM),
        ("hu_norfolk_aodl_q36", NOT_A_PROBLEM),
        ("hu_norfolk_aodl_q37", NOT_A_PROBLEM),
        ("hu_norfolk_aodl_q38", MODERATE),
        ("hu_norfolk_diffiactivities_q39", VERY_MILD),
        ("hu_norfolk_diffiactivities_q40", VERY_MILD),
        ("hu_norfolk_diffiactivities_q41", VERY_MILD),
        ("hu_norfolk_diffiactivities_q42", VERY_MILD),
        ("hu_norfolk_diffiactivities_q43", VERY_MILD),
        ("hu_norfolk_phyemohealth_q44", NOT_AT_ALL),
        ("hu_norfolk_phyemohealth_q45", NOT_AT_ALL),
        ("hu_norfolk_phyemohealth_q46", NOT_AT_ALL),
        ("hu_norfolk_phyemohealth_q47", NOT_AT_ALL),
        ("hu_norfolk_phyemohealth_q48", EXCELLENT),
        ("hu_norfolk_phyemohealth_q49", ABOUT_SAME),
        ("hu_norfolk_phyemohealth_q50", MODERATELY),
        ("hu_norfolk_phyemohealth_q51", MODERATELY),
        ("hu_norfolk_phyemohealth_q52", MODERATELY),
        ("hu_norfolk_generic_q10", ""),
    ]
    for question_id, answer in question_ids:
        answers.append(
            {
                QuestionnaireAnswer.ANSWER_TEXT: answer,
                QuestionnaireAnswer.QUESTION_ID: question_id,
                QuestionnaireAnswer.QUESTION: f"{question_id}: In the past 4 weeks, has pain kept you awake or woken you at night?",
            }
        )

    return answers


def sample_norfolk_questionnaire_module_data() -> dict:
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        Questionnaire.QUESTIONNAIRE_ID: "613bb29ed393b8b116d45d31",
        Questionnaire.MODULE_CONFIG_ID: "613bb279d393b8b116d45d30",
        Questionnaire.ANSWERS: sample_norfolk_answers(),
        ModuleConfig.MODULE_NAME: "Norfolk QOL-DN",
        Primitive.MODULE_ID: NorfolkQuestionnaireModule.moduleId,
        Questionnaire.QUESTIONNAIRE_NAME: "Norfolk QOL-DN",
    }


def sample_norfolk_questionnaire_missing_answers() -> dict:
    answers = sample_norfolk_answers()
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        Questionnaire.QUESTIONNAIRE_ID: "613bb29ed393b8b116d45d31",
        Questionnaire.MODULE_CONFIG_ID: "613bb279d393b8b116d45d30",
        Questionnaire.ANSWERS: answers[:6],
        ModuleConfig.MODULE_NAME: "Norfolk QOL-DN",
        Primitive.MODULE_ID: NorfolkQuestionnaireModule.moduleId,
        Questionnaire.QUESTIONNAIRE_NAME: "Norfolk QOL-DN",
    }


def sample_sf36_question_map() -> dict:
    return {
        "sf36_general_health_q1": {
            "format": "TEXTCHOICE",
            "options": [
                {"label": "Excellent", "weight": 100},
                {"label": "Very good", "weight": 75},
                {"label": "Good", "weight": 50},
                {"label": "Fair", "weight": 25},
                {"label": "Poor", "weight": 0},
            ],
        },
        "sf36_physical_health_problems_q14": {
            "format": "BOOLEAN",
            "order": 1,
            "text": "Accomplished less than you would like",
        },
        "sf36_physical_health_problems_q15": {
            "format": "BOOLEAN",
            "order": 1,
            "text": "Were limited in the <b>kind</b> of work or other activities",
        },
    }


def sample_body_measurement():
    return {
        **common_fields(),
        "type": BodyMeasurement.__name__,
        BodyMeasurement.VISCERAL_FAT: 10,
        BodyMeasurement.TOTAL_BODY_FAT: 50,
        BodyMeasurement.WAIST_CIRCUMFERENCE: 50,
        BodyMeasurement.HIP_CIRCUMFERENCE: 50,
    }


def sample_cvd_risk_score_questionnaire():
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        Questionnaire.QUESTIONNAIRE_ID: "613bb279d393b8b116d65d22",
        Questionnaire.QUESTIONNAIRE_NAME: "CVD",
        Questionnaire.ANSWERS: [
            {
                QuestionnaireAnswer.QUESTION_ID: "cvd_sleep_hours",
                QuestionnaireAnswer.QUESTION: "About how many hours of sleep do you usually get in 24 hours?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.NUMERIC.value,
                QuestionnaireAnswer.ANSWER_TEXT: "7",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "cvd_resting_heart_rate",
                QuestionnaireAnswer.QUESTION: "What is your Resting Heart Rate?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.NUMERIC_UNIT.value,
                QuestionnaireAnswer.ANSWER_TEXT: "95",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "cvd_hip_waist_circumference",
                QuestionnaireAnswer.ANSWER_TEXT: "90, 90",
                QuestionnaireAnswer.QUESTION: "What is your waist and hip circumference?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.COMPOSITE.value,
                QuestionnaireAnswer.COMPOSITE_ANSWER: {
                    "waistCircumference": "90",
                    "hipCircumference": "90",
                },
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "cvd_drink_alcohol",
                QuestionnaireAnswer.QUESTION: "How often do you drink alcohol?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.SINGLE.value,
                QuestionnaireAnswer.CHOICES: [i.value for i in AlcoholIntake],
                QuestionnaireAnswer.SELECTED_CHOICES: [
                    AlcoholIntake.SPECIAL_OCCASIONS.value,
                    AlcoholIntake.ONE_TO_THREE_TIMES_A_MONTH.value,
                ],
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "cvd_smoke",
                QuestionnaireAnswer.QUESTION: "Do you currently smoke?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.BOOLEAN.value,
                QuestionnaireAnswer.VALUE: True,
                QuestionnaireAnswer.ANSWER_TEXT: "Yes",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "cvd_walking_pace",
                QuestionnaireAnswer.QUESTION: "How would you describe your usual walking pace?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.SINGLE.value,
                QuestionnaireAnswer.CHOICES: [i.value for i in WalkingPace],
                QuestionnaireAnswer.SELECTED_CHOICES: [WalkingPace.BRISK_PACE.value],
                QuestionnaireAnswer.ANSWER_TEXT: WalkingPace.STEADY_AVERAGE_PACE.value,
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "cvd_overall_health",
                QuestionnaireAnswer.QUESTION: "In general, how would you rate your overall health?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.MULTIPLE.value,
                QuestionnaireAnswer.CHOICES: [i.value for i in OverallHealth],
                QuestionnaireAnswer.SELECTED_CHOICES: [OverallHealth.GOOD.value],
                QuestionnaireAnswer.ANSWER_TEXT: OverallHealth.GOOD.value,
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "cvd_conditions",
                QuestionnaireAnswer.QUESTION: "Have you been diagnosed with any of the following conditions?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.MULTIPLE.value,
                QuestionnaireAnswer.CHOICES: [i.value for i in ExistingCondition],
                QuestionnaireAnswer.SELECTED_CHOICES: [
                    ExistingCondition.DIABETES.value,
                    ExistingCondition.HIGH_BLOOD_PRESSURE.value,
                ],
                QuestionnaireAnswer.ANSWER_TEXT: ExistingCondition.DIABETES.value,
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "cvd_symptoms",
                QuestionnaireAnswer.QUESTION: "Do you experience any of the following symptoms?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.MULTIPLE.value,
                QuestionnaireAnswer.CHOICES: [i.value for i in ExistingSymptom],
                QuestionnaireAnswer.SELECTED_CHOICES: [
                    ExistingSymptom.ABDOMINAL_AND_PELVIC_PAIN.value
                ],
                QuestionnaireAnswer.ANSWER_TEXT: ExistingSymptom.ABDOMINAL_AND_PELVIC_PAIN.value,
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "cvd_medications",
                QuestionnaireAnswer.QUESTION: "Do you take any of the following medications?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.MULTIPLE.value,
                QuestionnaireAnswer.CHOICES: [i.value for i in CurrentMedication],
                QuestionnaireAnswer.SELECTED_CHOICES: [
                    CurrentMedication.CHOLESTEROL_LOWERING_MEDICATION.value,
                    CurrentMedication.BLOOD_PRESSURE_MEDICATION.value,
                ],
                QuestionnaireAnswer.ANSWER_TEXT: f"{CurrentMedication.CHOLESTEROL_LOWERING_MEDICATION.value},{CurrentMedication.BLOOD_PRESSURE_MEDICATION.value}",
            },
            {
                QuestionnaireAnswer.QUESTION_ID: "cvd_close_relatives",
                QuestionnaireAnswer.QUESTION: "Do any of your close relatives have a heart disease?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.MULTIPLE.value,
                QuestionnaireAnswer.CHOICES: [i.value for i in FamilyHeartDisease],
                QuestionnaireAnswer.SELECTED_CHOICES: [
                    FamilyHeartDisease.MOTHER.value,
                    FamilyHeartDisease.SIBLING.value,
                ],
                QuestionnaireAnswer.ANSWER_TEXT: f"{FamilyHeartDisease.MOTHER.value},{FamilyHeartDisease.SIBLING.value}",
            },
        ],
    }


def sample_questionnaire_with_other_option():
    return {
        **common_fields(),
        "questionnaireId": "749e6294-034e-4366-a9c9-83027d5c0fe5",
        "moduleConfigId": "5f15af1967af6dcbc05e2790",
        "type": Questionnaire.__name__,
        Questionnaire.QUESTIONNAIRE_ID: "613bb279d393b8b116d65d12",
        Questionnaire.QUESTIONNAIRE_NAME: "Sample",
        Questionnaire.ANSWERS: [
            {
                QuestionnaireAnswer.QUESTION_ID: "sample_overall_health",
                QuestionnaireAnswer.QUESTION: "In general, how would you rate your overall health?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.MULTIPLE.value,
                QuestionnaireAnswer.CHOICES: [i.value for i in OverallHealth]
                + ["OTHER"],
                QuestionnaireAnswer.SELECTED_CHOICES: [
                    OverallHealth.GOOD.value,
                    "OTHER",
                ],
                QuestionnaireAnswer.ANSWER_TEXT: OverallHealth.GOOD.value,
                QuestionnaireAnswer.OTHER_TEXT: "Other option 1, Other option 2,Other option 3",
            },
        ],
    }


def sample_questionnaire_with_autocomplete_option():
    return {
        **common_fields(),
        "questionnaireId": "749e6294-034e-4366-a9c9-83027d5c0fe5",
        "moduleConfigId": "5f15af1967af6dcbc05e2790",
        "type": Questionnaire.__name__,
        Questionnaire.QUESTIONNAIRE_ID: "613bb279d393b8b116d65d12",
        Questionnaire.QUESTIONNAIRE_NAME: "Sample",
        Questionnaire.ANSWERS: [
            {
                QuestionnaireAnswer.QUESTION_ID: "sample_overall_health",
                QuestionnaireAnswer.QUESTION: "In general, how would you rate your overall health?",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.AUTOCOMPLETE_TEXT.value,
                QuestionnaireAnswer.ANSWERS_LIST: [i.value for i in OverallHealth],
                QuestionnaireAnswer.ANSWER_TEXT: "",
            },
        ],
    }


def sample_questionnaire_with_media():
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        Questionnaire.QUESTIONNAIRE_ID: "5f15af1967af6dcbc05e2792",
        "moduleConfigId": "5f15af1967af6dcbc05e2792",
        Questionnaire.QUESTIONNAIRE_NAME: "Sample",
        Questionnaire.ANSWERS: [
            {
                QuestionnaireAnswer.QUESTION_ID: "sample_media_question",
                QuestionnaireAnswer.QUESTION: "Upload file",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.MEDIA.value,
                QuestionnaireAnswer.FILES_LIST: [
                    {
                        QuestionnaireAnswerMediaFile.MEDIA_TYPE: QuestionnaireAnswerMediaType.FILE.value,
                        QuestionnaireAnswerMediaFile.FILE: "613bb279d393b8b116d65d12",
                    }
                ],
            },
        ],
    }


def sample_steps_deprecated(value=200):
    return {
        **common_fields(),
        "type": Step.__name__,
        Step.VALUE: value,
        Step.DATA_TYPE: "MULTIPLE_VALUE",
        Step.MULTIPLE_VALUES: [
            {
                "id": "5b5279d1e303d394db6ea0f8",
                "p": {"0": 50, "15": 50, "30": 50, "45": 100},
                "d": "2019-06-30T00:00:00Z",
            }
        ],
        Step.RAW_DATA_OBJECT: {
            FlatBufferS3Object.KEY: "sample",
            FlatBufferS3Object.BUCKET: "sample",
            FlatBufferS3Object.REGION: "sample",
            FlatBufferS3Object.FBS_VERSION: 1,
        },
    }


def sample_steps(value=100):
    return {
        **common_fields(),
        "type": Step.__name__,
        Step.VALUE: value,
        Step.DATA_TYPE: "MULTIPLE_VALUE",
        Step.MULTIPLE_VALUES: [
            {
                "id": "5b5279d1e303d394db6ea0f8",
                "h": {"0": value},
                "d": "2019-06-30T00:00:00Z",
            }
        ],
        Step.RAW_DATA_OBJECT: {
            FlatBufferS3Object.KEY: "sample",
            FlatBufferS3Object.BUCKET: "sample",
            FlatBufferS3Object.REGION: "sample",
            FlatBufferS3Object.FBS_VERSION: 1,
        },
    }


def sample_symptom(severity: int = 1):
    return {
        **common_fields(),
        "type": Symptom.__name__,
        Symptom.COMPLEX_VALUES: [
            {
                ComplexSymptomValue.NAME: "Persistent cough",
                ComplexSymptomValue.SEVERITY: severity,
            },
            {
                ComplexSymptomValue.NAME: "Diarrhoea",
                ComplexSymptomValue.SEVERITY: 3,
            },
            {
                ComplexSymptomValue.NAME: "Difficulty sleeping",
                ComplexSymptomValue.SEVERITY: 4,
            },
        ],
    }


def sample_lysholm_and_tegner():
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        Questionnaire.QUESTIONNAIRE_ID: "611dffd20d4e78155ae591e8",
        Questionnaire.ANSWERS: [
            {
                QuestionnaireAnswer.ANSWER_TEXT: "I have no limp when I walk",
                QuestionnaireAnswer.QUESTION_ID: "lysholm_limp",
                QuestionnaireAnswer.QUESTION: "Section 1 - LIMP ",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "I do not use a cane or crutches",
                QuestionnaireAnswer.QUESTION_ID: "lysholm_cane_or_crutches",
                QuestionnaireAnswer.QUESTION: "Section 2 - Using cane or crutches",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "I have no locking and no catching sensation in my knee",
                QuestionnaireAnswer.QUESTION_ID: "lysholm_locking_sensation",
                QuestionnaireAnswer.QUESTION: "Section 3 - Locking sensation in the knee",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "My knee never gives way",
                QuestionnaireAnswer.QUESTION_ID: "lysholm_givingway_sensation",
                QuestionnaireAnswer.QUESTION: "Section 4 - Giving way sensation from the knee",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "I have no pain in my knee",
                QuestionnaireAnswer.QUESTION_ID: "lysholm_pain",
                QuestionnaireAnswer.QUESTION: "Section 5 - Pain",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "I have no swelling in my knee",
                QuestionnaireAnswer.QUESTION_ID: "lysholm_swelling",
                QuestionnaireAnswer.QUESTION: "Section 6 - Swelling",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "I have no problems climbing stairs",
                QuestionnaireAnswer.QUESTION_ID: "lysholm_climbing_stairs",
                QuestionnaireAnswer.QUESTION: "Section 7 - Climbing stairs",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "I cannot squat beyond a 90° bend in my knee",
                QuestionnaireAnswer.QUESTION_ID: "lysholm_squatting",
                QuestionnaireAnswer.QUESTION: "Section 8 - Squatting",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Level 10 <br> Competitive sports - soccer, football, rugby (national elite)",
                QuestionnaireAnswer.QUESTION_ID: "tegner_activity_level_before",
                QuestionnaireAnswer.QUESTION: "Please select the highest level of activity that you participated in BEFORE YOUR INJURY",
            },
            {
                QuestionnaireAnswer.ANSWER_TEXT: "Level 10 <br> Competitive sports - soccer, football, rugby (national elite)",
                QuestionnaireAnswer.QUESTION_ID: "tegner_activity_level_current",
                QuestionnaireAnswer.QUESTION: "Please select the highest level of activity that you are CURRENTLY able to participate in",
            },
        ],
        Questionnaire.MODULE_ID: "LysholmTegner",
        Questionnaire.QUESTIONNAIRE_NAME: "LysholmTegner",
        Questionnaire.MODULE_CONFIG_ID: "a844f829a543393adbba0abb",
    }


def sample_ikdc_answers() -> list:
    answers = []
    # we need a lot of questions in order to pass validation and calculate scores
    text_question_ids = [
        "ikdc_symptoms_pain_q1",
        "ikdc_symptoms_stifness_q1",
        "ikdc_symptoms_swelling_q1",
        "ikdc_symptoms_giveway_q1",
        "ikdc_symptoms_giveway_q2",
        "ikdc_sports_q1",
        "ikdc_sports_q2",
        "ikdc_sports_q3",
        "ikdc_sports_q4",
        "ikdc_sports_q5",
        "ikdc_sports_q6",
        "ikdc_sports_q7",
        "ikdc_sports_q8",
        "ikdc_sports_q9",
        "ikdc_sports_q10",
    ]
    for question_id in text_question_ids:
        answers.append(
            {
                QuestionnaireAnswer.ANSWER_TEXT: f"hu_{question_id}_a2",
                QuestionnaireAnswer.QUESTION_ID: question_id,
                QuestionnaireAnswer.QUESTION: f"{question_id}: Some tricky, question",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.SINGLE.value,
                QuestionnaireAnswer.SELECTED_CHOICES: [f"hu_{question_id}_a2"],
                QuestionnaireAnswer.CHOICES: [],
            }
        )

    scale_question_ids = [
        "ikdc_symptoms_pain_q2",
        "ikdc_symptoms_pain_q3",
        "ikdc_function_q1",
        "ikdc_function_q2",
    ]
    for question_id in scale_question_ids:
        answers.append(
            {
                QuestionnaireAnswer.LOWER_BOUND: 0,
                QuestionnaireAnswer.UPPER_BOUND: 10,
                QuestionnaireAnswer.VALUE: "5",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.SCALE.value,
                QuestionnaireAnswer.QUESTION_ID: question_id,
                QuestionnaireAnswer.QUESTION: f"{question_id}: Some tricky, question",
            }
        )

    return answers


def sample_ikdc_inavlid_scale_format_answers() -> list:
    answers = []
    # we need a lot of questions in order to pass validation and calculate scores
    text_question_ids = [
        "ikdc_symptoms_pain_q1",
        "ikdc_symptoms_stifness_q1",
        "ikdc_symptoms_swelling_q1",
        "ikdc_symptoms_giveway_q1",
        "ikdc_symptoms_giveway_q2",
        "ikdc_sports_q1",
        "ikdc_sports_q2",
        "ikdc_sports_q3",
        "ikdc_sports_q4",
        "ikdc_sports_q5",
        "ikdc_sports_q6",
        "ikdc_sports_q7",
        "ikdc_sports_q8",
        "ikdc_sports_q9",
        "ikdc_sports_q10",
    ]
    for question_id in text_question_ids:
        answers.append(
            {
                QuestionnaireAnswer.ANSWER_TEXT: f"hu_{question_id}_a2",
                QuestionnaireAnswer.QUESTION_ID: question_id,
                QuestionnaireAnswer.QUESTION: f"{question_id}: Some tricky, question",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
                QuestionnaireAnswer.SELECTION_CRITERIA: QuestionAnswerSelectionCriteria.SINGLE.value,
                QuestionnaireAnswer.SELECTED_CHOICES: [f"hu_{question_id}_a2"],
                QuestionnaireAnswer.CHOICES: [],
            }
        )

    scale_question_ids = [
        "ikdc_symptoms_pain_q2",
        "ikdc_symptoms_pain_q3",
        "ikdc_function_q1",
        "ikdc_function_q2",
    ]
    for question_id in scale_question_ids:
        answers.append(
            {
                QuestionnaireAnswer.LOWER_BOUND: 0,
                QuestionnaireAnswer.UPPER_BOUND: 10,
                QuestionnaireAnswer.VALUE: "value",
                QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.SCALE.value,
                QuestionnaireAnswer.QUESTION_ID: question_id,
                QuestionnaireAnswer.QUESTION: f"{question_id}: Some tricky, question",
            }
        )

    return answers


def sample_ikdc(invalid: bool = False):
    if invalid:
        return {
            **common_fields(),
            "type": Questionnaire.__name__,
            Questionnaire.QUESTIONNAIRE_ID: "611dffd20d4e78155ae591e8",
            Questionnaire.ANSWERS: sample_ikdc_inavlid_scale_format_answers(),
            Questionnaire.MODULE_ID: IKDCModule.moduleId,
            Questionnaire.QUESTIONNAIRE_NAME: IKDCModule.moduleId,
            Questionnaire.MODULE_CONFIG_ID: "61c444ca4618f7287a1c1bc6",
        }
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        Questionnaire.QUESTIONNAIRE_ID: "611dffd20d4e78155ae591e8",
        Questionnaire.ANSWERS: sample_ikdc_answers(),
        Questionnaire.MODULE_ID: IKDCModule.moduleId,
        Questionnaire.QUESTIONNAIRE_NAME: IKDCModule.moduleId,
        Questionnaire.MODULE_CONFIG_ID: "61c444ca4618f7287a1c1bc6",
    }


def sample_oacs_answers():

    return [
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Much worse",
            QuestionnaireAnswer.QUESTION_ID: "oacs_2",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "Your ability to walk compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Worse",
            QuestionnaireAnswer.QUESTION_ID: "oacs_3",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "Your ability to walk up stairs compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Better",
            QuestionnaireAnswer.QUESTION_ID: "oacs_4",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "Your ability to walk down stairs compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Much worse",
            QuestionnaireAnswer.QUESTION_ID: "oacs_5",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "Your strength compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Worse",
            QuestionnaireAnswer.QUESTION_ID: "oacs_6",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "How comfortable you feel when sitting compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Better",
            QuestionnaireAnswer.QUESTION_ID: "oacs_7",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "Your pain in the affected area compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Better",
            QuestionnaireAnswer.QUESTION_ID: "oacs_8",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "Your pain in the affected area when walking compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "The same",
            QuestionnaireAnswer.QUESTION_ID: "oacs_9",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "Your appetite compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Better",
            QuestionnaireAnswer.QUESTION_ID: "oacs_10",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "Your mood compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Better",
            QuestionnaireAnswer.QUESTION_ID: "oacs_11",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "Your energy level compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Better",
            QuestionnaireAnswer.QUESTION_ID: "oacs_12",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "Your sleep compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Worse",
            QuestionnaireAnswer.QUESTION_ID: "oacs_13",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "How you feel overall compared to before the operation?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "The same",
            QuestionnaireAnswer.QUESTION_ID: "oacs_14",
            QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.TEXTCHOICE.value,
            QuestionnaireAnswer.QUESTION: "Your pain when trying to sleep compared to before the operation?",
        },
    ]


def sample_oars_answers():

    return [
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Strongly disagree",
            QuestionnaireAnswer.QUESTION_ID: "oars_1",
            QuestionnaireAnswer.QUESTION: "I've felt unwell",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            QuestionnaireAnswer.QUESTION_ID: "oars_2",
            QuestionnaireAnswer.QUESTION: "I've felt tired",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            QuestionnaireAnswer.QUESTION_ID: "oars_3",
            QuestionnaireAnswer.QUESTION: "I've felt faint",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            QuestionnaireAnswer.QUESTION_ID: "oars_4",
            QuestionnaireAnswer.QUESTION: "It's been painful in the affected area",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Disagree",
            QuestionnaireAnswer.QUESTION_ID: "oars_5",
            QuestionnaireAnswer.QUESTION: "I've had pain at night in the affected area",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Strongly disagree",
            QuestionnaireAnswer.QUESTION_ID: "oars_6",
            QuestionnaireAnswer.QUESTION: "The affected area has felt swollen",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Strongly disagree",
            QuestionnaireAnswer.QUESTION_ID: "oars_7",
            QuestionnaireAnswer.QUESTION: "I've had difficulty getting into bed",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Strongly disagree",
            QuestionnaireAnswer.QUESTION_ID: "oars_8",
            QuestionnaireAnswer.QUESTION: "I've not been able to stand",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Neither agree nor disagree",
            QuestionnaireAnswer.QUESTION_ID: "oars_9",
            QuestionnaireAnswer.QUESTION: "I've not been able to walk",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Neither agree nor disagree",
            QuestionnaireAnswer.QUESTION_ID: "oars_10",
            QuestionnaireAnswer.QUESTION: "I've not slept well",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Neither agree nor disagree",
            QuestionnaireAnswer.QUESTION_ID: "oars_11",
            QuestionnaireAnswer.QUESTION: "I've found it difficult to sleep",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Agree",
            QuestionnaireAnswer.QUESTION_ID: "oars_12",
            QuestionnaireAnswer.QUESTION: "I've not been able to sleep due to the pain in the affected area",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Agree",
            QuestionnaireAnswer.QUESTION_ID: "oars_13",
            QuestionnaireAnswer.QUESTION: "I've felt sick",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Agree",
            QuestionnaireAnswer.QUESTION_ID: "oars_14",
            QuestionnaireAnswer.QUESTION: "I've lost my appetite",
        },
    ]


def sample_oacs(invalid: bool = False):
    if invalid:
        return {
            **common_fields(),
            "type": Questionnaire.__name__,
            Questionnaire.QUESTIONNAIRE_ID: "611dffd20d4e78155ae591e8",
            Questionnaire.ANSWERS: sample_oacs_answers()[:11],
            Questionnaire.MODULE_ID: OACSModule.moduleId,
            Questionnaire.QUESTIONNAIRE_NAME: OACSModule.moduleId,
            Questionnaire.MODULE_CONFIG_ID: "613bb279d393b8b116d65d72",
        }
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        Questionnaire.QUESTIONNAIRE_ID: "611dffd20d4e78155ae591e8",
        Questionnaire.ANSWERS: sample_oacs_answers(),
        Questionnaire.MODULE_ID: OACSModule.moduleId,
        Questionnaire.QUESTIONNAIRE_NAME: OACSModule.moduleId,
        Questionnaire.MODULE_CONFIG_ID: "613bb279d393b8b116d65d72",
    }


def sample_oars(invalid: bool = False):
    if invalid:
        return {
            **common_fields(),
            "type": Questionnaire.__name__,
            Questionnaire.QUESTIONNAIRE_ID: "611dffd20d4e78155ae591e8",
            Questionnaire.ANSWERS: sample_oars_answers()[:10],
            Questionnaire.MODULE_ID: OARSModule.moduleId,
            Questionnaire.QUESTIONNAIRE_NAME: OARSModule.moduleId,
            Questionnaire.MODULE_CONFIG_ID: "61c449ca4618f7227a1c1bc6",
        }
    return {
        **common_fields(),
        "type": Questionnaire.__name__,
        Questionnaire.QUESTIONNAIRE_ID: "611dffd20d4e78155ae591e8",
        Questionnaire.ANSWERS: sample_oars_answers(),
        Questionnaire.MODULE_ID: OARSModule.moduleId,
        Questionnaire.QUESTIONNAIRE_NAME: OARSModule.moduleId,
        Questionnaire.MODULE_CONFIG_ID: "61c449ca4618f7227a1c1bc6",
    }
