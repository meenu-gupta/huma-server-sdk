from dataclasses import field
from enum import Enum

from sdk import convertibleclass
from sdk.common.utils.convertible import default_field, meta
from sdk.common.utils.validators import validate_range


@convertibleclass
class ConfigurationField:
    parameter: str = default_field()
    name: str = default_field()


class DayAnchor(Enum):
    REGISTRATION_DATE = "REGISTRATION_DATE"
    CONSENT_DATE = "CONSENT_DATE"


@convertibleclass
class DeploymentLevelConfiguration:
    TARGET_CONSENTED_MONTHLY = "targetConsentedMonthly"
    TARGET_CONSENTED = "targetConsented"
    DAY_0_ANCHOR = "day0Anchor"
    TARGET_COMPLETED = "targetCompleted"

    targetConsentedMonthly: int = default_field(
        metadata=meta(validator=validate_range(0, 5000))
    )
    targetConsented: int = default_field(
        metadata=meta(validator=validate_range(1, 5000))
    )
    day0Anchor: DayAnchor = field(default=DayAnchor.REGISTRATION_DATE)
    targetCompleted: int = default_field(
        metadata=meta(validator=validate_range(1, 5000))
    )

    nameMapping = [
        ConfigurationField(
            parameter=TARGET_CONSENTED_MONTHLY, name="Monthly consented target"
        ),
        ConfigurationField(parameter=TARGET_CONSENTED, name="Total consented Target"),
        ConfigurationField(parameter=DAY_0_ANCHOR, name="Anchor date"),
        ConfigurationField(parameter=TARGET_COMPLETED, name="Target completed"),
    ]
