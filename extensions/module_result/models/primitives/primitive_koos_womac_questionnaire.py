from extensions.module_result.models.primitives import Primitive
from sdk.common.utils.convertible import convertibleclass, required_field


@convertibleclass
class WOMAC(Primitive):
    SYMPTOM_PREFIX = "koos_symptom"
    PAIN_PREFIX = "koos_pain"
    ADL_PREFIX = "koos_function"
    PAIN_SCORE = "painScore"
    SYMPTOMS_SCORE = "symptomsScore"
    ADL_SCORE = "adlScore"
    TOTAL_SCORE = "totalScore"

    painScore: float = required_field()
    symptomsScore: float = required_field()
    adlScore: float = required_field()
    totalScore: float = required_field()


@convertibleclass
class KOOS(Primitive):
    SYMPTOM_PREFIX = "koos_symptom"
    PAIN_PREFIX = "koos_pain"
    ADL_PREFIX = "koos_function"
    SPORT_RECREATION_PREFIX = "koos_sports"
    QUALITY_OF_LIFE_PREFIX = "koos_quality"
    SPORT_RECREATION = "sportRecreation"
    PAIN_SCORE = "painScore"
    SYMPTOMS_SCORE = "symptomsScore"
    SPORT_RECREATION_SCORE = "sportRecreationScore"
    ADL_SCORE = "adlScore"
    QUALITY_OF_LIFE_SCORE = "qualityOfLifeScore"

    adlScore: float = required_field()
    qualityOfLifeScore: float = required_field()
    painScore: float = required_field()
    symptomsScore: float = required_field()
    sportRecreationScore: float = required_field()
