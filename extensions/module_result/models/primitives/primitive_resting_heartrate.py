"""model for resting heart rate object"""

from sdk.common.utils.convertible import convertibleclass, meta, required_field
from .primitive import Primitive


@convertibleclass
class RestingHeartRate(Primitive):
    """RestingHeartRate model"""

    VALUE = "value"

    value: int = required_field(metadata=meta(value_to_field=int))
