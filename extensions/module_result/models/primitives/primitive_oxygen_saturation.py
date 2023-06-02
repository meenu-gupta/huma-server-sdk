"""model for oxygen saturation object"""
from dataclasses import field


from sdk.common.utils.convertible import convertibleclass, meta, required_field
from sdk.common.utils.validators import validate_range
from .primitive import HumaMeasureUnit, Primitive


@convertibleclass
class OxygenSaturation(Primitive):
    VALUE = "value"
    VALUE_UNIT = "valueUnit"

    value: float = required_field(
        metadata=meta(validate_range(0.7, 1), value_to_field=float),
    )
    valueUnit: str = field(
        default=HumaMeasureUnit.OXYGEN_SATURATION.value,
        metadata=meta(HumaMeasureUnit),
    )
