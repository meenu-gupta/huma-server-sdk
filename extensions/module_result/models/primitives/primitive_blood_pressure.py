"""model for blood pressure object"""
from dataclasses import field

from extensions.module_result.module_result_utils import AggregateFunc
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    ConvertibleClassValidationError,
    required_field,
    default_field,
)
from sdk.common.utils.validators import validate_entity_name, validate_range
from .primitive import Primitive, HumaMeasureUnit


@convertibleclass
class BloodPressure(Primitive):
    """BloodPressure model"""

    DIASTOLIC_VALUE = "diastolicValue"
    SYSTOLIC_VALUE = "systolicValue"
    DIASTOLIC_VALUE_UNIT = "diastolicValueUnit"

    ALLOWED_AGGREGATE_FUNCS = (AggregateFunc.AVG, AggregateFunc.MIN, AggregateFunc.MAX)
    AGGREGATION_FIELDS = (DIASTOLIC_VALUE, SYSTOLIC_VALUE)

    diastolicValue: int = required_field(
        metadata=meta(
            validate_range(30, 130),
            value_to_field=int,
        ),
    )
    systolicValue: int = required_field(
        metadata=meta(
            validate_range(60, 260),
            value_to_field=int,
        ),
    )
    unitSi: str = default_field(metadata=meta(validate_entity_name))
    diastolicValueUnit: str = field(
        default=HumaMeasureUnit.BLOOD_PRESSURE.value, metadata=meta(HumaMeasureUnit)
    )
    systolicValueUnit: str = field(
        default=HumaMeasureUnit.BLOOD_PRESSURE.value,
        metadata=meta(HumaMeasureUnit),
    )

    @classmethod
    def validate(cls, instance):
        if instance.diastolicValue > instance.systolicValue:
            raise ConvertibleClassValidationError(
                "Diastolic pressure can't be higher than systolic pressure"
            )
