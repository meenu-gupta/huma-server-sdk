""" Model for C-Score object """
from datetime import datetime
from enum import Enum

from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import default_datetime_meta
from .primitive import Primitive


class KeyAreaType(Enum):
    SLEEP = "SLEEP"
    SELF_RATED_HEALTH = "SELF_RATED_HEALTH"
    COGNITION = "COGNITION"
    TOBACCO_AND_ALCOHOL = "TOBACCO_AND_ALCOHOL"
    BODY = "BODY"
    CVD_HEALTH = "CVD_HEALTH"
    TOBACCO_ONLY = "TOBACCO_ONLY"
    ALCOHOL_ONLY = "ALCOHOL_ONLY"


@convertibleclass
class KeyAreaItem:
    SUBMISSION_DATE_TIME = "submissionDateTime"

    class Status(Enum):
        VERY_POOR = "VERY_POOR"
        POOR = "POOR"
        AVERAGE = "AVERAGE"
        GOOD = "GOOD"
        VERY_GOOD = "VERY_GOOD"
        NILL = "NILL"

    keyArea: KeyAreaType = required_field()
    messageLine: str = required_field()
    status: Status = required_field()
    value: int = required_field(metadata=meta(value_to_field=int))
    submissionDateTime: datetime = default_field(metadata=default_datetime_meta())


@convertibleclass
class HScore(Primitive):
    """CScore model."""

    class HScoreStatus(Enum):
        HIGH = "HIGH"
        MODERATE = "MODERATE"
        LOW = "LOW"

    # Value is not required as it will be calculated in the backend, rather than be submitted by apps.
    value: int = required_field(metadata=meta(value_to_field=int))
    topValue: int = required_field(metadata=meta(value_to_field=int))
    bottomValue: int = required_field(metadata=meta(value_to_field=int))

    # HIGH MODERATE LOW
    status: HScoreStatus = required_field()
    keyAreasItems: list[KeyAreaItem] = default_field()
