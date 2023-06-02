from extensions.common.s3object import FlatBufferS3Object
from sdk.common.utils.convertible import convertibleclass, required_field
from .primitive import Primitive


@convertibleclass
class HighFrequencyStep(Primitive):
    """High frequency model represent flatbuffer format"""

    STEPS_OBJECT = "stepsObject"

    stepsObject: FlatBufferS3Object = required_field()
