from dataclasses import field
from datetime import datetime

from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field


@convertibleclass
class Stat:
    VALUE = "value"
    UNIT = "unit"

    value: int = required_field(metadata=meta(value_to_field=round))
    unit: str = field(default="")


@convertibleclass
class DeploymentStats:
    COMPLETED_COUNT = "completedCount"
    COMPLETED_TASK = "completedTask"
    CONSENTED_COUNT = "consentedCount"
    ENROLLED_COUNT = "enrolledCount"
    PATIENT_COUNT = "patientCount"
    UPDATE_DATE_TIME = "updateDateTime"

    completedCount: Stat = default_field()
    completedTask: Stat = default_field()
    consentedCount: Stat = default_field()
    enrolledCount: Stat = default_field()
    patientCount: Stat = default_field()
    updateDateTime: datetime = field(default_factory=datetime.utcnow)
