"""model for my body measurement object"""
from dataclasses import field

from sdk.common.utils.convertible import convertibleclass, meta, default_field
from sdk.common.utils.validators import validate_range
from .primitive import Primitive, HumaMeasureUnit


@convertibleclass
class BodyMeasurement(Primitive):
    """BodyMeasurement model."""

    VISCERAL_FAT = "visceralFat"
    TOTAL_BODY_FAT = "totalBodyFat"
    WAIST_CIRCUMFERENCE = "waistCircumference"
    WAIST_CIRCUMFERENCE_UNIT = "waistCircumferenceUnit"
    HIP_CIRCUMFERENCE = "hipCircumference"
    HIP_CIRCUMFERENCE_UNIT = "hipCircumferenceUnit"
    WAIST_TO_HIP_RATIO = "waistToHipRatio"

    visceralFat: float = default_field(metadata=meta(value_to_field=float))
    totalBodyFat: float = default_field(metadata=meta(value_to_field=float))
    waistCircumference: float = default_field(
        metadata=meta(validate_range(0, 500), value_to_field=float),
    )
    waistCircumferenceUnit: str = field(
        default=HumaMeasureUnit.WAIST_CIRCUMFERENCE.value,
        metadata=meta(HumaMeasureUnit),
    )
    hipCircumference: float = default_field(
        metadata=meta(validate_range(0, 500), value_to_field=float)
    )
    hipCircumferenceUnit: str = field(
        default=HumaMeasureUnit.HIP_CIRCUMFERENCE.value,
        metadata=meta(HumaMeasureUnit),
    )
    waistToHipRatio: float = default_field(metadata=meta(value_to_field=float))

    def get_field_value(self, field_name: str, default_value: float = 0) -> float:
        val = getattr(self, field_name, None)
        return val if val is not None else default_value
