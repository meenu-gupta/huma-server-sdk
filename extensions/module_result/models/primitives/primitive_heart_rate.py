"""model for heart rate object"""
from dataclasses import field
from enum import Enum

from extensions.common.s3object import S3Object
from extensions.module_result.module_result_utils import AggregateFunc
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import validate_range
from .primitive import HumaMeasureUnit, Primitive
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class HeartRate(Primitive):
    """HeartRate model"""

    class HeartRateType(Enum):
        UNSPECIFIED = "UNSPECIFIED"
        RESTING = "RESTING"
        HIGH_FREQ = "HIGH_FREQ"

    VALUE = "value"
    CLASSIFICATION = "classification"
    ALLOWED_AGGREGATE_FUNCS = (AggregateFunc.AVG, AggregateFunc.MIN, AggregateFunc.MAX)
    AGGREGATION_FIELDS = (VALUE,)

    value: int = required_field(metadata=meta(validate_range(0, 250)))
    heartRateType: HeartRateType = default_field()

    classification: str = default_field()
    source: str = default_field()

    # additional fields for PPG collection
    variabilityAVNN: int = default_field()
    variabilitySDNN: int = default_field()
    variabilityRMSSD: int = default_field()
    variabilityPNN50: float = default_field(metadata=meta(value_to_field=float))
    variabilityprcLF: float = default_field(metadata=meta(value_to_field=float))
    confidence: int = default_field()
    goodIBI: int = default_field()
    rawDataObject: S3Object = default_field()
    valueUnit: str = field(
        default=HumaMeasureUnit.HEART_RATE.value,
        metadata=meta(HumaMeasureUnit),
    )
    metadata: QuestionnaireMetadata = default_field()
