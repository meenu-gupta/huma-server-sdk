"""model for step object"""
from enum import Enum

from extensions.common.s3object import FlatBufferS3Object
from extensions.module_result.common.models import MultipleHourValuesData
from extensions.module_result.module_result_utils import AggregateFunc
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from .primitive import Primitive


@convertibleclass
class Step(Primitive):
    """Step model"""

    VALUE = "value"
    WEEKLY_TOTAL = "weeklyTotal"
    MULTIPLE_VALUES = "multipleValues"
    RAW_DATA_OBJECT = "rawDataObject"
    DATA_TYPE = "dataType"

    ALLOWED_AGGREGATE_FUNCS = (
        AggregateFunc.AVG,
        AggregateFunc.MIN,
        AggregateFunc.MAX,
        AggregateFunc.SUM,
    )
    AGGREGATION_FIELDS = ("value",)

    class DataType(Enum):
        MULTIPLE_VALUE = "MULTIPLE_VALUE"

    value: int = required_field(metadata=meta(value_to_field=int))
    weeklyTotal: int = default_field()
    multipleValues: list[MultipleHourValuesData] = default_field()
    rawDataObject: FlatBufferS3Object = default_field()
    dataType: DataType = default_field()
