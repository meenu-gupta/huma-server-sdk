"""model for pulse oximetry object"""

from sdk.common.utils.convertible import convertibleclass, meta, required_field
from sdk.common.utils.validators import validate_range
from .primitive import Primitive


@convertibleclass
class PulseOximetry(Primitive):
    """PulseOximetry model"""

    value: float = required_field(
        metadata=meta(validate_range(0.5, 1.05), value_to_field=float)
    )
