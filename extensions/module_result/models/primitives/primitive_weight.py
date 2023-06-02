"""model for weight object"""
from dataclasses import field

from extensions.module_result.module_result_utils import AggregateFunc
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import validate_range
from .primitive import HumaMeasureUnit, Primitive


@convertibleclass
class Weight(Primitive):
    """Weight model"""

    VALUE = "value"

    ALLOWED_AGGREGATE_FUNCS = (AggregateFunc.AVG, AggregateFunc.MIN, AggregateFunc.MAX)
    AGGREGATION_FIELDS = ("value",)

    value: float = required_field(
        metadata=meta(validate_range(20, 300), value_to_field=float)
    )
    valueUnit: str = field(
        default=HumaMeasureUnit.WEIGHT.value, metadata=meta(HumaMeasureUnit)
    )
    originalValue: float = default_field(metadata=meta(value_to_field=float))
    originalUnit: str = default_field()
