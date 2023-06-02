from extensions.module_result.models.primitives import Primitive
from sdk.common.utils.convertible import convertibleclass, required_field


@convertibleclass
class KCCQ(Primitive):
    PHYSICAL_LIMITATION = "physicalLimitation"
    SYMPTOM_STABILITY = "symptomStability"
    SYMPTOM_FREQUENCY = "symptomFrequency"
    SYMPTOM_BURDEN = "symptomBurden"
    TOTAL_SYMPTOM_SCORE = "totalSymptomScore"
    SELF_EFFICACY = "selfEfficacy"
    QUALITY_OF_LIFE = "qualityOfLife"
    SOCIAL_LIMITATION = "socialLimitation"
    OVERALL_SUMMARY_SCORE = "overallSummaryScore"
    CLINICAL_SUMMARY_SCORE = "clinicalSummaryScore"

    SUBSCALE_PHYSICAL_LIMITATION = "physical_limitation"
    SUBSCALE_SYMPTOM_STABILITY = "symptom_stability"
    SUBSCALE_SYMPTOM_FREQUENCY = "symptom_frequency"
    SUBSCALE_SYMPTOM_BURDEN = "symptom_burden"
    SUBSCALE_SELF_EFFICACY = "self_efficacy"
    SUBSCALE_QUALITY_OF_LIFE = "quality_of_life"
    SUBSCALE_SOCIAL_LIMITATION = "social_limitation"

    physicalLimitation: float = required_field()
    symptomStability: float = required_field()
    symptomFrequency: float = required_field()
    symptomBurden: float = required_field()
    totalSymptomScore: float = required_field()
    selfEfficacy: float = required_field()
    qualityOfLife: float = required_field()
    socialLimitation: float = required_field()
    overallSummaryScore: float = required_field()
    clinicalSummaryScore: float = required_field()

    _partitioned_answers = None

    @property
    def partitioned_answers(self):
        return self._partitioned_answers

    @partitioned_answers.setter
    def partitioned_answers(self, partitioned_answers: list[dict]):
        self._partitioned_answers = partitioned_answers
