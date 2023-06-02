"""model for my journal object"""

from sdk.common.utils.convertible import convertibleclass, meta, required_field
from sdk.common.utils.validators import validate_len
from .primitive import Primitive


@convertibleclass
class Journal(Primitive):
    """Journal model."""

    value: str = required_field(metadata=meta(validate_len(min=1)))
