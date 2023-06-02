"""model for high frequency heart rate object"""
from enum import Enum

from sdk.common.utils.convertible import convertibleclass, default_field
from . import Primitive
from .primitive_heart_rate import HeartRate
from extensions.module_result.common.models import MultipleValuesData


@convertibleclass
class HighFrequencyHeartRate(HeartRate, Primitive):
    """High Frequency Heart Rate model"""

    MULTIPLE_VALUES = "multipleValues"
    DATA_TYPE = "dataType"

    class DataType(Enum):
        MULTIPLE_VALUE = "MULTIPLE_VALUE"
        PPG_VALUE = "PPG_VALUE"  # Patient has taken heart rate reading from Camera
        SINGLE_VALUE = "SINGLE_VALUE"

    multipleValues: list[MultipleValuesData] = default_field()
    dataType: DataType = default_field()

    def post_init(self):
        if self.rawDataObject:
            self.heartRateType = self.HeartRateType.HIGH_FREQ
