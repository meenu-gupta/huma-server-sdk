"""
    Model class for a device enabled medication data point.
"""
from enum import Enum

from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from .primitive import Primitive


@convertibleclass
class DeviceMedicationTracker(Primitive):
    class CompletionStatus(Enum):
        NONE = "NONE"
        PARTIAL = "PARTIAL"
        FULL = "FULL"

    class AdministrationMethod(Enum):
        NEBULIZER = "NEBULIZER"
        INHALER = "INHALER"

    # medication administration method
    administrationMethod: AdministrationMethod = default_field()
    # field to track whether the medication activity was fully completed or partial
    completionStatus: CompletionStatus = required_field()
    # the duration in milliseconds of the medication event/activity
    doseDuration: int = default_field()
    # the unit to use for the stored value of the medication used/administered Ex: g, kg, ml, min, sec, etc.
    doseUnit: str = default_field()
    # medication being administered/taken
    medicationName: str = default_field()
    # the actual value to store for the medication consumed/administered
    value: float = required_field(metadata=meta(float, value_to_field=float))
