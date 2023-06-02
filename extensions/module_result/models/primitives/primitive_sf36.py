from extensions.module_result.models.primitives import Primitive
from sdk import convertibleclass
from sdk.common.utils.convertible import default_field


@convertibleclass
class SF36(Primitive):
    PHYSICAL_FUNCTIONING_SCORE = "physicalFunctioningScore"
    LIMITATIONS_PHYSICAL_HEALTH_SCORE = "limitationsPhysicalHealthScore"
    LIMITATIONS_EMOTIONAL_PROBLEMS_SCORE = "limitationsEmotionalProblemsScore"
    ENERGY_FATIGUE_SCORE = "energyFatigueScore"
    EMOTIONAL_WELL_BEING_SCORE = "emotionalWellBeingScore"
    SOCIAL_FUNCTIONING_SCORE = "socialFunctioningScore"
    PAIN_SCORE = "painScore"
    GENERAL_HEALTH_SCORE = "generalHealthScore"

    SUBSCALE_GENERAL_HEALTH = "general_health"
    SUBSCALE_PHYSICAL_FUNCTIONING = "limitation_activities"
    SUBSCALE_LIMITATIONS_PHYSICAL_HEALTH = "physical_health_problems"
    SUBSCALE_LIMITATIONS_EMOTIONAL_PROBLEMS = "emotional_health_problems"
    SUBSCALE_SOCIAL_FUNCTIONING = "social_activities"
    SUBSCALE_PAIN = "pain"
    SUBSCALE_ENERGY_FATIGUE = "energy_fatigue"
    SUBSCALE_EMOTIONAL_WELL_BEING = "emotional_well_being"

    physicalFunctioningScore: float = default_field()
    limitationsPhysicalHealthScore: float = default_field()
    limitationsEmotionalProblemsScore: float = default_field()
    energyFatigueScore: float = default_field()
    emotionalWellBeingScore: float = default_field()
    socialFunctioningScore: float = default_field()
    painScore: float = default_field()
    generalHealthScore: float = default_field()

    _partitioned_answers = None

    @property
    def answers(self):
        return self._partitioned_answers
