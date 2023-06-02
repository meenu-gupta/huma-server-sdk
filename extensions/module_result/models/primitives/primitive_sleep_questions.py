"""model for sleep questions"""
from enum import Enum
from typing import Optional

from extensions.module_result.module_result_utils import PoorToExcellent
from sdk.common.utils.convertible import convertibleclass, required_field
from .primitive import Primitive


@convertibleclass
class SleepQuestions(Primitive):
    """SleepQuestions model"""

    class TiredScore(Enum):
        LESS_THAN_NORMAL = "LESS_THAN_NORMAL"
        SLIGHTLY_LESS_THAN_NORMAL = "SLIGHTLY_LESS_THAN_NORMAL"
        NO_MORE_THAN_NORMAL = "NO_MORE_THAN_NORMAL"
        SLIGHTLY_MORE_THAN_NORMAL = "SLIGHTLY_MORE_THAN_NORMAL"
        MORE_THAN_NORMAL = "MORE_THAN_NORMAL"

    sleepQualityScore: PoorToExcellent = required_field()
    tiredScore: TiredScore = required_field()

    hoursSleep: int = required_field()
    minutesSleep: int = required_field()

    def get_estimated_value(self) -> Optional[float]:
        hours = self.hoursSleep or 0
        minutes = self.minutesSleep or 0

        value = None
        if hours > 0 or minutes > 0:
            value = (hours * 60 + minutes) / 60.0

        return value
