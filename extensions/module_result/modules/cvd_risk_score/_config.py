from copy import deepcopy
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Iterable, Callable

from extensions.module_result.common.enums import BiologicalSex
from extensions.module_result.models.primitives.cvd_risk_score import (
    AlcoholIntake,
    CVDRiskScore,
    ExistingCondition,
    FamilyHeartDisease,
    CurrentMedication,
    ExistingSymptom,
    OverallHealth,
    WalkingPace,
)
from extensions.module_result.modules.cvd_risk_score.score_engine_enums import (
    AlcoholIntake as ScoreEngineAlcoholIntake,
    CurrentMedication as ScoreEngineCurrentMedication,
    Gender,
    OtherDisease,
    OverallHealth as ScoreEngineOverallHealth,
    Symptom,
    RelativesHeartDiseaseEnum,
    TobaccoSmoking,
    WalkingPace as ScoreEngineWalkingPace,
)


@dataclass
class Answer:
    text: str
    targetField: str = None
    value: int = None
    exclusive: bool = None


@dataclass
class QuestionConfig:
    question: str
    answerType: str
    primitiveField: str
    targetField: str = None
    answers: list[Answer] = None

    def match_answer(self, answer) -> Optional[Answer]:
        if not self.answers:
            return

        return next((o for o in self.answers if o.text == answer), None)


class CVDRiskScoreConfig:
    """Singleton class for CVD Risk Score configs"""

    class AnswerType(Enum):
        NUMERIC = auto()
        SINGLE = auto()
        MULTIPLE = auto()

    _instance = None

    cvd_age: QuestionConfig = None
    cvd_sex: QuestionConfig = None
    cvd_sleep_hours: QuestionConfig = None
    cvd_resting_heart_rate: QuestionConfig = None
    cvd_waist_circumference: QuestionConfig = None
    cvd_hip_circumference: QuestionConfig = None
    cvd_hip_waist_circumference: QuestionConfig = None
    cvd_drink_alcohol: QuestionConfig = None
    cvd_smoke: QuestionConfig = None
    cvd_walking_pace: QuestionConfig = None
    cvd_overall_health: QuestionConfig = None
    cvd_conditions: QuestionConfig = None
    cvd_symptoms: QuestionConfig = None
    cvd_medications: QuestionConfig = None
    cvd_close_relatives: QuestionConfig = None

    def __new__(cls):
        if cls._instance:
            return cls._instance

        instance = super().__new__(cls)
        config = deepcopy(_question_config)
        for question_id, conf in config.items():
            if not hasattr(instance, question_id):
                continue

            conf["answers"] = _convert_answers(conf.get("answers"))
            question = QuestionConfig(**conf)
            setattr(instance, question_id, question)

        cls._instance = instance
        return cls._instance

    def __getitem__(self, item) -> Optional[QuestionConfig]:
        return getattr(self, item, None)

    def __iter__(self) -> Iterable[QuestionConfig]:
        return (getattr(self, f) for f in self.__annotations__)

    def get(self, item: str):
        return self[item]

    def find(self, func: Callable[[QuestionConfig], bool]) -> Optional[QuestionConfig]:
        return next(filter(func, self), None)


def _convert_answers(answers: Optional[dict]) -> Optional[list[Answer]]:
    if not answers:
        return answers

    return [Answer(**a) for a in answers]


_question_config: dict[str, dict] = {
    "cvd_age": {
        "question": "What is your age?",
        "answerType": CVDRiskScoreConfig.AnswerType.NUMERIC,
        "targetField": "age",
        "primitiveField": CVDRiskScore.AGE,
    },
    "cvd_sex": {
        "question": "What was your biological sex at birth?",
        "answerType": CVDRiskScoreConfig.AnswerType.SINGLE,
        "answers": [
            {"text": BiologicalSex.MALE, "value": Gender.MALE},
            {"text": BiologicalSex.FEMALE, "value": Gender.FEMALE},
            {"text": BiologicalSex.OTHER, "value": Gender.OTHER},
            {"text": BiologicalSex.NOT_SPECIFIED, "value": Gender.NOT_SPECIFIED},
        ],
        "targetField": "gender",
        "primitiveField": CVDRiskScore.SEX,
    },
    "cvd_sleep_hours": {
        "question": "About how many hours of sleep do you get in every 24 hours?",
        "answerType": CVDRiskScoreConfig.AnswerType.NUMERIC,
        "targetField": CVDRiskScore.SLEEP_DURATION,
        "primitiveField": CVDRiskScore.SLEEP_DURATION,
    },
    "cvd_resting_heart_rate": {
        "question": "What is your resting heart rate?",
        "answerType": CVDRiskScoreConfig.AnswerType.NUMERIC,
        "targetField": CVDRiskScore.HEART_RATE,
        "primitiveField": CVDRiskScore.HEART_RATE,
    },
    "cvd_waist_circumference": {
        "question": "",
        "answerType": CVDRiskScoreConfig.AnswerType.NUMERIC,
        "targetField": CVDRiskScore.WAIST_CIRCUMFERENCE,
        "primitiveField": CVDRiskScore.WAIST_CIRCUMFERENCE,
    },
    "cvd_hip_circumference": {
        "question": "",
        "answerType": CVDRiskScoreConfig.AnswerType.NUMERIC,
        "targetField": CVDRiskScore.HIP_CIRCUMFERENCE,
        "primitiveField": CVDRiskScore.HIP_CIRCUMFERENCE,
    },
    "cvd_hip_waist_circumference": {
        "question": "What is your waist-to-hip ratio?",
        "answerType": CVDRiskScoreConfig.AnswerType.NUMERIC,
        "targetField": CVDRiskScore.WAIST_TO_HIP_RATIO,
        "primitiveField": CVDRiskScore.WAIST_TO_HIP_RATIO,
    },
    "cvd_drink_alcohol": {
        "question": "About how often do you drink alcohol?",
        "answerType": CVDRiskScoreConfig.AnswerType.SINGLE,
        "answers": [
            {"text": AlcoholIntake.DAILY, "value": ScoreEngineAlcoholIntake.DRINKER},
            {
                "text": AlcoholIntake.THREE_OR_FOUR_TIMES_A_WEEK,
                "value": ScoreEngineAlcoholIntake.DRINKER,
            },
            {
                "text": AlcoholIntake.ONCE_OR_TWICE_A_WEEK,
                "value": ScoreEngineAlcoholIntake.DRINKER,
            },
            {
                "text": AlcoholIntake.ONE_TO_THREE_TIMES_A_MONTH,
                "value": ScoreEngineAlcoholIntake.DRINKER,
            },
            {
                "text": AlcoholIntake.SPECIAL_OCCASIONS,
                "value": ScoreEngineAlcoholIntake.DRINKER,
            },
            {"text": AlcoholIntake.NEVER, "value": ScoreEngineAlcoholIntake.NEVER},
        ],
        "targetField": CVDRiskScore.ALCOHOL_INTAKE,
        "primitiveField": CVDRiskScore.ALCOHOL_INTAKE,
    },
    "cvd_smoke": {
        "question": "Do you currently smoke?",
        "answerType": CVDRiskScoreConfig.AnswerType.SINGLE,
        "answers": [
            {"text": True, "value": TobaccoSmoking.SMOKER},
            {"text": False, "value": TobaccoSmoking.NON_SMOKER},
        ],
        "targetField": "tobaccoSmoking",
        "primitiveField": CVDRiskScore.SMOKING_STATUS,
    },
    "cvd_walking_pace": {
        "question": "How would you describe your usual walking pace?",
        "answerType": CVDRiskScoreConfig.AnswerType.SINGLE,
        "answers": [
            {"text": WalkingPace.SLOW_PACE, "value": ScoreEngineWalkingPace.OTHER},
            {
                "text": WalkingPace.STEADY_AVERAGE_PACE,
                "value": ScoreEngineWalkingPace.STEADY_AVERAGE_PACE,
            },
            {
                "text": WalkingPace.BRISK_PACE,
                "value": ScoreEngineWalkingPace.BRISK_PACE,
            },
        ],
        "targetField": "walkingPace",
        "primitiveField": CVDRiskScore.WALKING_PACE,
    },
    "cvd_overall_health": {
        "question": "In general how would you rate your overall health?",
        "answerType": CVDRiskScoreConfig.AnswerType.SINGLE,
        "answers": [
            {
                "text": OverallHealth.EXCELLENT,
                "value": ScoreEngineOverallHealth.EXCELLENT,
            },
            {
                "text": OverallHealth.GOOD,
                "value": ScoreEngineOverallHealth.GOOD,
            },
            {
                "text": OverallHealth.FAIR,
                "value": ScoreEngineOverallHealth.OTHER,
            },
            {
                "text": OverallHealth.POOR,
                "value": ScoreEngineOverallHealth.POOR,
            },
        ],
        "targetField": "overallHealth",
        "primitiveField": CVDRiskScore.OVERALL_HEALTH,
    },
    "cvd_conditions": {
        "question": "Have you been diagnosed with any of the following conditions? (You can select more than one answer)",
        "answerType": CVDRiskScoreConfig.AnswerType.MULTIPLE,
        "answers": [
            {
                "text": ExistingCondition.HIGH_BLOOD_PRESSURE,
                "value": OtherDisease.HIGH_BLOOD_PRESSURE,
            },
            {
                "text": ExistingCondition.ATRIAL_FIBRILLATION_OR_FLUTTER,
                "value": OtherDisease.ATRIAL_FIBRILLATION_OR_FLUTTER,
            },
            {
                "text": ExistingCondition.LEUKAEMIA_LYMPHOMA_MYELOMA,
                "value": OtherDisease.LEUKAEMIA_LYMPHOMA_MYELOMA,
            },
            {
                "text": ExistingCondition.DEPRESSION,
                "value": OtherDisease.DEPRESSION,
            },
            {
                "text": ExistingCondition.OTHER_HEART_ARRHYTHMIAS,
                "value": OtherDisease.OTHER_HEART_ARRHYTHMIAS,
            },
            {
                "text": ExistingCondition.DIABETES,
                "value": OtherDisease.DIABETES,
            },
            {"text": ExistingCondition.NONE_OF_THE_ABOVE, "exclusive": True},
        ],
        "targetField": "otherDiseases",
        "primitiveField": CVDRiskScore.EXISTING_CONDITIONS,
    },
    "cvd_symptoms": {
        "question": "Do you experience any of the following symptoms? (You can select more than one answer)",
        "answerType": CVDRiskScoreConfig.AnswerType.MULTIPLE,
        "answers": [
            {"text": ExistingSymptom.BREATHLESSNESS, "value": Symptom.BREATHLESSNESS},
            {
                "text": ExistingSymptom.DIZZINESS_OR_GIDDINESS,
                "value": Symptom.DIZZINESS_OR_GIDDINESS,
            },
            {
                "text": ExistingSymptom.LOSS_OF_CONSCIOUSNESS_OR_COLLAPSE,
                "value": Symptom.LOSS_OF_CONSCIOUSNESS_OR_COLLAPSE,
            },
            {
                "text": ExistingSymptom.ABDOMINAL_AND_PELVIC_PAIN,
                "value": Symptom.ABDOMINAL_AND_PELVIC_PAIN,
            },
            {"text": ExistingSymptom.NONE_OF_THE_ABOVE, "exclusive": True},
        ],
        "targetField": "symptoms",
        "primitiveField": CVDRiskScore.EXISTING_SYMPTOMS,
    },
    "cvd_medications": {
        "question": "Do you take any of the following medications? (You can select more than one answer)",
        "answerType": CVDRiskScoreConfig.AnswerType.MULTIPLE,
        "answers": [
            {
                "text": CurrentMedication.CHOLESTEROL_LOWERING_MEDICATION,
                "value": ScoreEngineCurrentMedication.CHOLESTEROL_LOWERING_MEDICATION,
            },
            {
                "text": CurrentMedication.BLOOD_PRESSURE_MEDICATION,
                "value": ScoreEngineCurrentMedication.BLOOD_PRESSURE_MEDICATION,
            },
            {
                "text": CurrentMedication.INSULIN,
                "value": ScoreEngineCurrentMedication.INSULIN,
            },
            {"text": CurrentMedication.NONE_OF_THE_ABOVE, "exclusive": True},
        ],
        "targetField": CVDRiskScore.CURRENT_MEDICATIONS,
        "primitiveField": CVDRiskScore.CURRENT_MEDICATIONS,
    },
    "cvd_close_relatives": {
        "question": "Does any of your close relatives have a heart disease? (You can select more than one answer)",
        "answerType": CVDRiskScoreConfig.AnswerType.MULTIPLE,
        "answers": [
            {
                "text": FamilyHeartDisease.FATHER,
                "value": RelativesHeartDiseaseEnum.FATHER,
            },
            {
                "text": FamilyHeartDisease.MOTHER,
                "value": RelativesHeartDiseaseEnum.MOTHER,
            },
            {
                "text": FamilyHeartDisease.SIBLING,
                "value": RelativesHeartDiseaseEnum.SIBLINGS,
            },
            {"text": FamilyHeartDisease.NONE_OF_THE_ABOVE, "exclusive": True},
        ],
        "targetField": "relativesHeartDisease",
        "primitiveField": CVDRiskScore.FAMILY_HEART_DISEASE,
    },
}
