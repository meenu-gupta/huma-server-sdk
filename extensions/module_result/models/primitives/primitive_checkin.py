"""model for checkin object"""

from sdk.common.utils.convertible import convertibleclass, meta, required_field
from .primitive import Primitive


@convertibleclass
class Checkin(Primitive):
    """Checkin model"""

    VALUE = "value"

    value: str = required_field(metadata=meta(str))
