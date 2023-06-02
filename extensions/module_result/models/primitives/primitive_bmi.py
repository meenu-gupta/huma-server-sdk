"""model for BMI object"""
from dataclasses import field

from extensions.module_result.module_result_utils import AggregateFunc
from sdk.common.utils.convertible import convertibleclass, meta, required_field
from .primitive import HumaMeasureUnit, Primitive


@convertibleclass
class BMI(Primitive):
    """BMI model"""

    VALUE = "value"

    ALLOWED_AGGREGATE_FUNCS = (AggregateFunc.AVG, AggregateFunc.MIN, AggregateFunc.MAX)
    AGGREGATION_FIELDS = ("value",)

    value: float = required_field(metadata=meta(value_to_field=float))
    valueUnit: str = field(
        default=HumaMeasureUnit.BMI.value,
        metadata=meta(HumaMeasureUnit),
    )
