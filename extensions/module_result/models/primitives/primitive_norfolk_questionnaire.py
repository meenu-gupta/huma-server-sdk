from extensions.module_result.models.primitives import Primitive
from sdk import convertibleclass
from sdk.common.utils.convertible import required_field, meta


@convertibleclass
class NORFOLK(Primitive):
    TOTAL_QOL_SCORE = "totalQolScore"
    PHYSICAL_FUNCTION_LARGER_FIBER = "physicalFunctionLargeFiber"
    ACTIVITIES_OF_DAILY_LIVING = "activitiesOfDailyLiving"
    SYMPTOMS = "symptoms"
    SMALL_FIBER = "smallFiber"
    AUTOMIC = "automic"

    totalQolScore: float = required_field(metadata=meta(value_to_field=float))
    physicalFunctionLargeFiber: float = required_field(
        metadata=meta(value_to_field=float)
    )
    activitiesOfDailyLiving: float = required_field(metadata=meta(value_to_field=float))
    symptoms: float = required_field(metadata=meta(value_to_field=float))
    smallFiber: float = required_field(metadata=meta(value_to_field=float))
    automic: float = required_field(metadata=meta(value_to_field=float))

    _answers = []

    @property
    def answers(self):
        return self._answers
