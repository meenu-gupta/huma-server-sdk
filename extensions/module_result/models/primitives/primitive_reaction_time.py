"""model for reaction time object"""
from typing import Optional

from extensions.module_result.module_result_utils import AggregateFunc
from sdk.common.utils.convertible import convertibleclass, meta, required_field
from .primitive import Primitive


@convertibleclass
class ReactionTime(Primitive):
    """ReactionTime model"""

    ALLOWED_AGGREGATE_FUNCS = (AggregateFunc.AVG, AggregateFunc.MIN, AggregateFunc.MAX)
    AGGREGATION_FIELDS = ("value",)

    value: float = required_field(
        metadata=meta(value_to_field=float)
    )  # in second(could fraction)

    def get_estimated_value(self) -> Optional[float]:  # return by millisecond
        return self.value * 1000.0
