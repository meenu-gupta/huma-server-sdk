"""model for timed up and go object"""

from sdk.common.utils.convertible import convertibleclass, meta, required_field
from .primitive import Primitive


@convertibleclass
class TimedUpAndGo(Primitive):
    """TimedUpAndGo model"""

    VALUE = "value"

    value: float = required_field(metadata=meta(value_to_field=float))
