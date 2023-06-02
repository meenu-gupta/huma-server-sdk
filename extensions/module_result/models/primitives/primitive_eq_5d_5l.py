from sdk.common.utils.convertible import (
    convertibleclass,
    default_field,
    meta,
)
from .primitive import Primitive


@convertibleclass
class EQ5D5L(Primitive):
    """EQ5D5L model."""

    INDEX_VALUE = "indexValue"
    HEALTH_STATE = "healthState"
    MOBILITY = "mobility"
    SELF_CARE = "selfCare"
    USUAL_ACTIVITIES = "usualActivities"
    PAIN = "pain"
    ANXIETY = "anxiety"
    EQ_VAS = "eqVas"

    indexValue: float = default_field()
    healthState: int = default_field()
    mobility: int = default_field(metadata=meta(value_to_field=int))
    selfCare: int = default_field(metadata=meta(value_to_field=int))
    usualActivities: int = default_field(metadata=meta(value_to_field=int))
    pain: int = default_field(metadata=meta(value_to_field=int))
    anxiety: int = default_field(metadata=meta(value_to_field=int))
    eqVas: int = default_field(metadata=meta(value_to_field=int))

    _scoring_answers = None

    @property
    def scoring_answers(self):
        return self._scoring_answers

    @scoring_answers.setter
    def scoring_answers(self, value):
        self._scoring_answers = value
