""" Model for Numeric Memory Primitive """
from typing import Optional

from extensions.module_result.module_result_utils import AggregateFunc
from sdk.common.utils.convertible import convertibleclass, required_field
from .primitive import Primitive


@convertibleclass
class NumericMemory(Primitive):
    """Numeric Memory model"""

    ALLOWED_AGGREGATE_FUNCS = (AggregateFunc.AVG, AggregateFunc.MIN, AggregateFunc.MAX)
    AGGREGATION_FIELDS = ("value",)

    value: int = required_field()

    def get_estimated_value(self) -> Optional[float]:
        return float(self.value)
