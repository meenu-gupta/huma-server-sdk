"""model for weight object"""
from dataclasses import field


from extensions.module_result.module_result_utils import AggregateFunc
from sdk.common.utils.convertible import convertibleclass, meta, required_field
from sdk.common.utils.validators import validate_range
from .primitive import HumaMeasureUnit, Primitive


@convertibleclass
class Height(Primitive):
    """Height model"""

    ALLOWED_AGGREGATE_FUNCS = (AggregateFunc.AVG, AggregateFunc.MIN, AggregateFunc.MAX)
    AGGREGATION_FIELDS = ("value",)

    value: float = required_field(
        metadata=meta(validate_range(100, 250), value_to_field=float)
    )
    valueUnit: str = field(
        default=HumaMeasureUnit.HEIGHT.value, metadata=meta(HumaMeasureUnit)
    )
