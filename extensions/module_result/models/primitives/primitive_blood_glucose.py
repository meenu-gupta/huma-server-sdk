"""model for blood glucose object"""
from dataclasses import field
from functools import lru_cache

from extensions.module_result.models.primitives.primitive import (
    HumaMeasureUnit,
    MeasureUnit,
)
from extensions.module_result.module_result_utils import AggregateFunc
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import validate_entity_name, validate_range
from .primitive import Primitive


@convertibleclass
class BloodGlucose(Primitive):
    """BloodGlucose model"""

    VALUE = "value"
    VALUE_UNIT = "valueUnit"

    ALLOWED_AGGREGATE_FUNCS = (AggregateFunc.AVG, AggregateFunc.MIN, AggregateFunc.MAX)
    AGGREGATION_FIELDS = ("value",)

    UNITS_CONVERTERS_MAP = {
        MeasureUnit.MILLIGRAMS_PER_DECILITRE: lambda x: x * 18,
        MeasureUnit.MILLIMOLES_PER_LITRE: lambda x: x / 18,
    }

    value: float = required_field(
        metadata=meta(validate_range(1, 26), value_to_field=float)
    )
    unitSi: str = default_field(metadata=meta(validate_entity_name))
    valueUnit: str = field(
        default=HumaMeasureUnit.BLOOD_GLUCOSE.value,
        metadata=meta(HumaMeasureUnit),
    )
    originalValue: float = default_field(metadata=meta(value_to_field=float))
    originalUnit: str = default_field()

    def get_value_by_unit(self, unit: MeasureUnit):
        if not unit or unit.value == self.valueUnit:
            return self.value

        if unit.value == self.originalUnit:
            return self.originalValue

        converter = self.UNITS_CONVERTERS_MAP.get(unit)
        if not converter:
            return self.value

        return converter(self.value)
