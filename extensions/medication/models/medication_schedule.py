"""model for Medication Schedule"""
from dataclasses import field
from enum import Enum

from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import validate_object_id, validate_range


@convertibleclass
class MedicationSchedule:
    """A MedicationSchedule describes a pattern of scheduled Medication doses to be taken by a user."""

    ID = "id"
    FREQUENCY = "frequency"
    PERIOD = "period"
    PERIOD_UNIT = "periodUnit"

    class PeriodUnit(Enum):
        DAILY = "DAILY"
        WEEKLY = "WEEKLY"
        MONTHLY = "MONTHLY"
        ANNUAL = "ANNUAL"

    FREQUENCY_MAPPING = {
        "DAILY": "a day",
        "WEEKLY": "a week",
        "MONTHLY": "a month",
        "ANNUAL": "a year",
    }

    id: str = default_field(metadata=meta(validate_object_id))
    frequency: int = required_field(metadata=meta(validate_range(1, 366)))
    period: int = field(default=1)
    periodUnit: PeriodUnit = required_field()

    def get_frequency_str(self) -> str:
        times = f"{str(self.frequency)} times"
        if self.frequency == 1:
            times = "once"
        return f"{times} {self.FREQUENCY_MAPPING[self.periodUnit.value]}"
