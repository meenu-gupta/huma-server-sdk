""" Model for C-Score object """
from sdk.common.utils.convertible import convertibleclass, meta, default_field
from .primitive import Primitive


@convertibleclass
class CScore(Primitive):
    """CScore model."""

    VALUE = "value"

    # Value is not required as it will be calculated in the backend, rather than be submitted by apps.
    value: int = default_field(metadata=meta(value_to_field=int))
