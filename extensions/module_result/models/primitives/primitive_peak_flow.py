""" Model for Peak Flow object """
from dataclasses import field

from extensions.authorization.models.user import User
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
class PeakFlow(Primitive):
    """Peak Flow model."""

    VALUE = "value"
    VALUE_PERCENT = "valuePercent"

    ALLOWED_AGGREGATE_FUNCS = (AggregateFunc.AVG, AggregateFunc.MIN, AggregateFunc.MAX)
    AGGREGATION_FIELDS = ("value", "valuePercent")

    value: int = required_field(
        metadata=meta(validate_range(300, 700), value_to_field=int),
    )
    valuePercent: float = default_field(metadata=meta(value_to_field=float))
    valueUnit: str = field(
        default=HumaMeasureUnit.PEAK_FLOW.value,
        metadata=meta(HumaMeasureUnit),
    )

    def calculate_percent(self, gender, age, height) -> float:
        if gender == User.Gender.FEMALE:
            value = ((height * 3.72 / 100 + 2.24) - age * 0.03) * 60
        else:
            value = ((height * 5.48 / 100 + 1.58) - age * 0.041) * 60

        return self.value / value * 100
