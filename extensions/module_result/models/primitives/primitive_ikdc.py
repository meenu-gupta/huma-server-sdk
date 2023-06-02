from extensions.module_result.models.primitives import Primitive
from sdk.common.utils.convertible import (
    meta,
    convertibleclass,
    default_field,
)
from sdk.common.utils.validators import validate_range


def ikdc_field(min: int = 0, max: int = 4):
    return default_field(
        metadata=meta(value_to_field=float, validator=validate_range(min, max))
    )


@convertibleclass
class Symptoms:
    PAIN_ACTIVITY = "painActivity"
    PAIN_HISTORY = "painHistory"
    PAIN_SEVERITY = "painSeverity"
    STIFFNESS_HISTORY = "stiffnessHistory"
    SWELLING_ACTIVITY = "swellingActivity"
    GIVE_WAY_LOCK = "giveWayLock"
    GIVE_WAY_ACTIVITY = "giveWayActivity"

    painActivity: float = ikdc_field()
    painHistory: float = ikdc_field(max=10)
    painSeverity: float = ikdc_field(max=10)
    stiffnessHistory: float = ikdc_field()
    swellingActivity: float = ikdc_field()
    giveWayLock: float = ikdc_field(max=1)
    giveWayActivity: float = ikdc_field()

    @staticmethod
    def field_to_id_map():
        return {
            Symptoms.PAIN_ACTIVITY: "ikdc_symptoms_pain_q1",
            Symptoms.PAIN_HISTORY: "ikdc_symptoms_pain_q2",
            Symptoms.PAIN_SEVERITY: "ikdc_symptoms_pain_q3",
            Symptoms.STIFFNESS_HISTORY: "ikdc_symptoms_stifness_q1",
            Symptoms.SWELLING_ACTIVITY: "ikdc_symptoms_swelling_q1",
            Symptoms.GIVE_WAY_LOCK: "ikdc_symptoms_giveway_q1",
            Symptoms.GIVE_WAY_ACTIVITY: "ikdc_symptoms_giveway_q2",
        }


@convertibleclass
class SportsActivity:
    HIGHEST_LEVEL = "highestLevel"
    STAIRS_UP = "stairsUp"
    STAIRS_DOWN = "stairsDown"
    KNEEL = "kneel"
    SQUAT = "squat"
    SIT = "sit"
    RISE = "rise"
    RUN = "run"
    JUMP_AND_LAND = "jumpAndLand"
    STOP_AND_START = "stopAndStart"

    highestLevel: float = ikdc_field()
    stairsUp: float = ikdc_field()
    stairsDown: float = ikdc_field()
    kneel: float = ikdc_field()
    squat: float = ikdc_field()
    sit: float = ikdc_field()
    rise: float = ikdc_field()
    run: float = ikdc_field()
    jumpAndLand: float = ikdc_field()
    stopAndStart: float = ikdc_field()

    @staticmethod
    def field_to_id_map():
        return {
            SportsActivity.HIGHEST_LEVEL: "ikdc_sports_q1",
            SportsActivity.STAIRS_UP: "ikdc_sports_q2",
            SportsActivity.STAIRS_DOWN: "ikdc_sports_q3",
            SportsActivity.KNEEL: "ikdc_sports_q4",
            SportsActivity.SQUAT: "ikdc_sports_q5",
            SportsActivity.SIT: "ikdc_sports_q6",
            SportsActivity.RISE: "ikdc_sports_q7",
            SportsActivity.RUN: "ikdc_sports_q8",
            SportsActivity.JUMP_AND_LAND: "ikdc_sports_q9",
            SportsActivity.STOP_AND_START: "ikdc_sports_q10",
        }


@convertibleclass
class KneeFunction:
    PRIOR = "prior"
    CURRENT = "current"

    prior: float = ikdc_field(max=10)
    current: float = ikdc_field(max=10)

    @staticmethod
    def field_to_id_map():
        return {
            KneeFunction.PRIOR: "ikdc_function_q1",
            KneeFunction.CURRENT: "ikdc_function_q2",
        }


@convertibleclass
class IKDC(Primitive):
    SYMPTOMS = "symptoms"
    SPORTS_ACTIVITY = "sportsActivity"
    KNEE_FUNCTION = "kneeFunction"
    VALUE = "value"

    symptoms: Symptoms = default_field()
    sportsActivity: SportsActivity = default_field()
    kneeFunction: KneeFunction = default_field()

    # total score
    value: float = default_field(metadata=meta(value_to_field=float))

    _scoring_answers = None

    @property
    def scoring_answers(self):
        return self._scoring_answers

    @scoring_answers.setter
    def scoring_answers(self, value):
        self._scoring_answers = value
