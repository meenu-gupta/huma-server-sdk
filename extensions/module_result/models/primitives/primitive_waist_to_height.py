""" Model for waist-to-height object """
from typing import Optional

from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    ConvertibleClassValidationError,
    required_field,
    default_field,
)
from .primitive import Primitive


@convertibleclass
class WaistToHeight(Primitive):
    """WaistToHeight model"""

    HEIGHT = "height"
    WAIST = "waist"
    VALUE = "value"

    height: float = required_field(metadata=meta(value_to_field=float))
    waist: float = default_field(metadata=meta(value_to_field=float))
    value: float = default_field(metadata=meta(value_to_field=float))

    @classmethod
    def validate(cls, instance):
        if instance.waist and instance.height and instance.waist > instance.height:
            raise ConvertibleClassValidationError("Waist can't be bigger than height")

        if not ((instance.height and instance.waist) or instance.value):
            raise ConvertibleClassValidationError(
                "One of value field or waist + height value should be present"
            )

        if not instance.value:
            instance.value = float(instance.waist) / float(instance.height)

    def get_estimated_value(self) -> Optional[float]:
        return float(self.value)
