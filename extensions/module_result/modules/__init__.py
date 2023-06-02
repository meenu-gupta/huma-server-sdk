from .awareness_training import AwarenessTrainingModule
from .az_screening_questionnaire import AZScreeningQuestionnaireModule
from .background_information import BackgroundInformationModule
from .blood_glucose import BloodGlucoseModule
from .blood_pressure import BloodPressureModule
from .bmi import BMIModule
from .breastfeeding_status import BreastFeedingStatusModule
from .breastfeeding_update import BreastFeedingUpdateModule
from .breathing import BreathingModule
from .breathlessness import BreathlessnessModule
from .bvi import BVIModule
from .covid19_daily_checkin import Covid19DailyCheckInModule
from .covid19_risk_score import Covid19RiskScoreModule
from .cvd_risk_score import CVDRiskScoreModule
from .daily_check_in import DailyCheckInModule
from .diabetes_distress_score import DiabetesDistressScoreModule
from .eq5d_5l import EQ5D5LModule
from .ecg_alive_cor import ECGAliveCorModule
from .ecg_module.ecg_healthkit import ECGHealthKitModule
from .fjs_hip_score import FJSHipScoreModule
from .fjs_knee_score import FJSKneeScoreModule
from .further_pregnancy_key_action_trigger import (
    AZFurtherPregnancyKeyActionTriggerModule,
)
from .general_anxiety_disorder import GeneralAnxietyDisorderModule
from .group_key_action_trigger import AZGroupKeyActionTriggerModule
from .health_score import HealthScoreModule
from .health_status import HealthStatusModule
from .heart_rate import HeartRateModule
from .height import HeightModule
from .high_frequency_heart_rate import HighFrequencyHeartRateModule
from .high_frequency_step import HighFrequencyStepModule
from .infant_follow_up import InfantFollowUpModule
from .ikdc import IKDCModule
from .journal import JournalModule
from .kccq import KCCQQuestionnaireModule
from .koos import KOOSQuestionnaireModule
from .lysholm_and_tegner import LysholmTegnerModule
from .medical_history import MedicalHistoryModule
from .medication import MedicationsModule
from .medication_tracker import MedicationTrackerModule
from .norfolk import NorfolkQuestionnaireModule
from .oacs import OACSModule
from .oars import OARSModule
from .other_vaccine import OtherVaccineModule
from .oxford_hip_score import OxfordHipScoreQuestionnaireModule
from .oxford_knee_score import OxfordKneeScoreQuestionnaireModule
from .oxygen_saturation import OxygenSaturationModule
from .peak_flow import PeakFlowModule
from .photo import PhotoModule
from .post_vaccination import PostVaccinationModule
from .pregnancy_follow_up import PregnancyFollowUpModule
from .pregnancy_status import PregnancyStatusModule
from .pregnancy_update import PregnancyUpdateModule
from .promis_global_health import PROMISGlobalHealthModule
from .pulse_oximetry import PulseOximetryModule
from .questionnaire import QuestionnaireModule
from .questionnaire_fever_and_pain_drugs import FeverAndPainDrugsModule
from .questionnaire_qol import AdditionalQoLModule
from .respiratory_rate import RespiratoryRateModule
from .resting_breathing_rate import RestingBreathingRateModule
from .resting_heart_rate import RestingHeartRateModule
from .revere_test import RevereTestModule
from .sf36_questionnaire import SF36QuestionnaireModule
from .step import StepModule
from .surgery_details import SurgeryDetailsModule
from .symptom import SymptomModule
from .temperature import TemperatureModule
from .vaccination_details import VaccinationDetailsModule
from .waist_to_height import WaistToHeightModule
from .weight import WeightModule

default_modules = (
    AZFurtherPregnancyKeyActionTriggerModule,
    AZGroupKeyActionTriggerModule,
    AZScreeningQuestionnaireModule,
    AdditionalQoLModule,
    AwarenessTrainingModule,
    BMIModule,
    BackgroundInformationModule,
    BloodGlucoseModule,
    BloodPressureModule,
    BreastFeedingStatusModule,
    BreastFeedingUpdateModule,
    BreathingModule,
    BreathlessnessModule,
    BVIModule,
    Covid19DailyCheckInModule,
    Covid19RiskScoreModule,
    CVDRiskScoreModule,
    DailyCheckInModule,
    DiabetesDistressScoreModule,
    EQ5D5LModule,
    ECGAliveCorModule,
    ECGHealthKitModule,
    FeverAndPainDrugsModule,
    FJSHipScoreModule,
    FJSKneeScoreModule,
    GeneralAnxietyDisorderModule,
    HealthScoreModule,
    HealthStatusModule,
    HeartRateModule,
    HeightModule,
    HighFrequencyHeartRateModule,
    HighFrequencyStepModule,
    IKDCModule,
    InfantFollowUpModule,
    JournalModule,
    KCCQQuestionnaireModule,
    KOOSQuestionnaireModule,
    LysholmTegnerModule,
    MedicalHistoryModule,
    MedicationTrackerModule,
    MedicationsModule,
    NorfolkQuestionnaireModule,
    OACSModule,
    OARSModule,
    OtherVaccineModule,
    OxfordHipScoreQuestionnaireModule,
    OxfordKneeScoreQuestionnaireModule,
    OxygenSaturationModule,
    PROMISGlobalHealthModule,
    PeakFlowModule,
    PhotoModule,
    PostVaccinationModule,
    PregnancyFollowUpModule,
    PregnancyStatusModule,
    PregnancyUpdateModule,
    PulseOximetryModule,
    QuestionnaireModule,
    RespiratoryRateModule,
    RestingBreathingRateModule,
    RestingHeartRateModule,
    RevereTestModule,
    SF36QuestionnaireModule,
    StepModule,
    SurgeryDetailsModule,
    SymptomModule,
    TemperatureModule,
    VaccinationDetailsModule,
    WaistToHeightModule,
    WeightModule,
)

rag_enabled_module_ids = [m.moduleId for m in default_modules if m.ragEnabled]
excluded_modules_ids_for_applying_default_disclaimer_config = [
    "SF36",
    "PROMISGlobalHealth",
    "KCCQ",
    "DiabetesDistressScore",
    "NORFOLK",
    "GeneralAnxietyDisorder",
    "FJSKnee",
    "FJSHip",
    "LysholmTegner",
    "KneeHealthIKDC",
    "KOOS",
    "OxfordHipScore",
    "OxfordKneeScore",
    "OACS",
    "OARS",
    "AwarenessTraining",
    "AZScreeningQuestionnaire",
    "BackgroundInformation",
    "ECGHealthKit",
    "HighFrequencyStep",
    "Step",
    "RevereTest",
    "SurgeryDetails",
]
excluded_questionnaire_types_for_applying_default_disclaimer_config = [
    "EQ5D_5L",
    "PAM",
    "PROMIS_PAIN",
    "PROMIS_PHYSICAL",
    "PROMIS_PHYSICAL_DE",
    "PROMIS_PAIN_DE",
    "OBSERVATION_NOTES",
    "PROMIS_PHYSICAL_ES",
    "PROMIS_PAIN_ES",
]
