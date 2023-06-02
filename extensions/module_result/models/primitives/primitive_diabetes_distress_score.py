from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from .primitive import Primitive


@convertibleclass
class DiabetesDistressScore(Primitive):
    """DiabetesDistressScore model."""

    TOTAL_DDS = "totalDDS"
    EMOTIONAL_BURDEN = "emotionalBurden"
    PHYSICIAN_DISTRESS = "physicianDistress"
    REGIMEN_DISTRESS = "regimenDistress"
    INTERPERSONAL_DISTRESS = "interpersonalDistress"

    totalDDS: float = required_field(metadata=meta(float))
    emotionalBurden: float = default_field(metadata=meta(float))
    physicianDistress: float = default_field(metadata=meta(float))
    regimenDistress: float = default_field(metadata=meta(float))
    interpersonalDistress: float = default_field(metadata=meta(float))
