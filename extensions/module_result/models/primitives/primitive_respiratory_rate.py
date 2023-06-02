"""model for Respiratory Rate object"""
from dataclasses import field

from extensions.module_result.module_result_utils import AggregateFunc
from sdk.common.utils.convertible import convertibleclass, meta, required_field
from sdk.common.utils.validators import validate_range
from .primitive import HumaMeasureUnit, Primitive


@convertibleclass
class RespiratoryRate(Primitive):
    """Respiratory Rate model"""

    VALUE = "value"

    ALLOWED_AGGREGATE_FUNCS = (AggregateFunc.AVG, AggregateFunc.MIN, AggregateFunc.MAX)
    AGGREGATION_FIELDS = ("value",)

    value: int = required_field(
        metadata=meta(validate_range(6, 30), value_to_field=int),
    )
    valueUnit: str = field(
        default=HumaMeasureUnit.RESPIRATORY_RATE.value,
        metadata=meta(HumaMeasureUnit),
    )
