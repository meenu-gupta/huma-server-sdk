""" Model for C-Score object """
from extensions.module_result.common.enums import Severity
from sdk.common.utils.convertible import convertibleclass, meta, default_field
from .primitive import Primitive


@convertibleclass
class Covid19RiskScore(Primitive):
    """CScore model."""

    STATUS = "status"
    VALUE = "value"

    # Value is not required as it will be calculated in the backend, rather than be submitted by apps.
    value: float = default_field(
        metadata=meta(value_to_field=lambda x: round(float(x))),
    )
    status: Severity = default_field()
