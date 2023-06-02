"""model for self health estimate object"""

from enum import Enum
from typing import Optional

from sdk.common.utils.convertible import convertibleclass, required_field
from .primitive import Primitive


class OverallHealthFeeling(Enum):
    POOR = 1
    FAIR = 2
    GOOD = 3
    EXCELLENT = 4


@convertibleclass
class SelfHealthRate(Primitive):
    """SelfHealthRate model"""

    value: OverallHealthFeeling = required_field()

    def get_estimated_value(self) -> Optional[float]:
        v = None
        if self.value == OverallHealthFeeling.POOR:
            v = 3.0
        elif self.value == OverallHealthFeeling.FAIR:
            v = 2.0
        elif self.value == OverallHealthFeeling.GOOD:
            v = 1.0
        elif self.value == OverallHealthFeeling.EXCELLENT:
            v = 0.0

        return v
