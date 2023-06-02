"""model for reaction time object"""

from sdk.common.utils.convertible import convertibleclass, meta, required_field
from .primitive import Primitive


@convertibleclass
class RestingBreathingRate(Primitive):
    """ReactionTime model"""

    value: int = required_field(metadata=meta(value_to_field=int))
