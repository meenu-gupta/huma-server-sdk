from enum import IntEnum

from extensions.common.s3object import S3Object, FlatBufferS3Object
from sdk import convertibleclass
from sdk.common.utils.convertible import required_field, meta, default_field
from .primitive import Primitive


class ECGClassification(IntEnum):
    # 5 and 7 are missing, because those are unacceptable values
    sinusRhythm = 1
    atrialFibrillation = 2
    inconclusiveHighHeartRate = 3
    inconclusiveLowHeartRate = 4
    inconclusiveOther = 6
    notSet = 8


@convertibleclass
class ECGReading:
    AVERAGE_HEART_RATE = "averageHeartRate"
    DATA_POINTS = "dataPoints"

    averageHeartRate: int = required_field(metadata=meta(value_to_field=int))
    dataPoints: FlatBufferS3Object = required_field()


@convertibleclass
class ECGHealthKit(Primitive):
    """ECG from Apple's HealthKit Model"""

    GENERATED_PDF = "generatedPDF"
    ECG_READING = "ecgReading"

    value: ECGClassification = required_field()
    ecgReading: ECGReading = required_field()
    generatedPDF: S3Object = default_field()
