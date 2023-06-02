"""model for smoke questions"""
from enum import Enum
from typing import Optional

from extensions.module_result.common.enums import SmokeStatus
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils.convertible import convertibleclass, required_field, default_field
from .primitive import Primitive


@convertibleclass
class SmokeQuestions(Primitive):
    """SmokeQuestions model"""

    class SmokerType(Enum):
        REGULAR_SMOKER = "REGULAR_SMOKER"
        SOCIAL_SMOKER = "SOCIAL_SMOKER"

    class SmokingPeriod(Enum):
        LESS_THAN_A_YEAR = "LESS_THAN_A_YEAR"
        FROM_1_to_5_YEARS = "FROM_1_to_5_YEARS"
        FROM_6_to_10_YEARS = "FROM_6_to_10_YEARS"
        FROM_11_to_15_YEARS = "FROM_11_to_15_YEARS"
        MORE_THAN_15_YEARS = "MORE_THAN_15_YEARS"

    class VapeStatus(Enum):
        YES_AND_I_STILL_DO = "YES_AND_I_STILL_DO"
        YES_BUT_I_QUIT = "YES_BUT_I_QUIT"
        NO = "NO"

    class VapePeriodic(Enum):
        RARELY = "RARELY"
        OCCASIONALLY = "OCCASIONALLY"
        OFTEN = "OFTEN"
        EVERY_DAY = "EVERY_DAY"

    smokeStatus: SmokeStatus = required_field()
    smokerType: SmokerType = default_field()
    smokingPeriod: SmokingPeriod = default_field()
    numberOfCigarettesPerDay: int = default_field()
    numberOfCigarettesPerMonth: int = default_field()

    vapeStatus: VapeStatus = required_field()
    vapePeriodic: VapePeriodic = default_field()

    @classmethod
    def validate(cls, instance: "SmokeQuestions"):
        if instance.smokeStatus != SmokeQuestions.SmokeStatus.NO:
            if (
                instance.smokerType == SmokeQuestions.SmokerType.REGULAR_SMOKER
                and not instance.numberOfCigarettesPerDay
            ):
                raise InvalidRequestException(
                    message="Regular smoker type needs numberOfCigarettesPerDay"
                )
            elif (
                instance.smokerType == SmokeQuestions.SmokerType.SOCIAL_SMOKER
                and not instance.numberOfCigarettesPerMonth
            ):
                raise InvalidRequestException(
                    message="Social smoker type needs numberOfCigarettesPerDay"
                )

    def get_estimated_value(self) -> Optional[float]:
        if self.smokeStatus == SmokeQuestions.SmokeStatus.NO:
            value = -2.0
        elif self.smokeStatus == SmokeQuestions.SmokeStatus.YES_BUT_I_QUIT:
            value = -1.0
        else:
            if self.smokerType == SmokeQuestions.SmokerType.REGULAR_SMOKER:
                value = float(self.numberOfCigarettesPerDay)
            elif self.smokerType == SmokeQuestions.SmokerType.SOCIAL_SMOKER:
                value = float(self.numberOfCigarettesPerMonth) / 30.0
            else:
                raise NotImplementedError
        return value
