"""model for sensor capture object"""
from enum import Enum

from extensions.common.s3object import S3Object
from sdk.common.utils.convertible import convertibleclass, meta, default_field
from .primitive import Primitive


@convertibleclass
class SensorCapture(Primitive):
    """SensorCapture model"""

    class MeasurementLocation(Enum):
        LEFT_FRONT_TROUSERS_POCKET = "LEFT_FRONT_TROUSERS_POCKET"
        RIGHT_FRONT_TROUSERS_POCKET = "RIGHT_FRONT_TROUSERS_POCKET"
        LEFT_BACK_TROUSERS_POCKET = "LEFT_BACK_TROUSERS_POCKET"
        RIGHT_BACK_TROUSERS_POCKET = "RIGHT_BACK_TROUSERS_POCKET"
        CHEST = "CHEST"
        DIAPHRAGM = "DIAPHRAGM"

    class SensorDataType(Enum):
        ACCELEROMETER = "ACCELEROMETER"
        GYROSCOPE = "GYROSCOPE"
        MICROPHONE = "MICROPHONE"
        PEDOMETER = "PEDOMETER"

    s3Object: S3Object = default_field(metadata=meta(S3Object, True))
    sanityCheck: bool = default_field(metadata=meta(bool, False))
    sanityCheckMessage: str = default_field(metadata=meta(False))
    measurementLocation: MeasurementLocation = default_field(metadata=meta(False))
    sensorDataTypes: list[SensorDataType] = default_field(metadata=meta(True))
    value: float = default_field(metadata=meta(float, False))
