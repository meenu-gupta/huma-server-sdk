"""model for timed walk object"""
from enum import Enum

from extensions.common.s3object import S3Object
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from .primitive import Primitive


@convertibleclass
class TimedWalk(Primitive):
    """TimedWalk model"""

    class MeasurementLocation(Enum):
        LEFT_POCKET = "LEFT_POCKET"
        RIGHT_POCKET = "RIGHT_POCKET"

    s3Object: S3Object = required_field(metadata=meta(S3Object))
    sanityCheck: bool = default_field()
    measurementLocation: MeasurementLocation = default_field()
