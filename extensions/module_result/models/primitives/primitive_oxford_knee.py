from dataclasses import field
from enum import IntEnum

from extensions.module_result.models.primitives import Primitive
from sdk.common.utils.convertible import (
    required_field,
    convertibleclass,
    meta,
    default_field,
)
from sdk.common.utils.validators import validate_range


class LegAffected(IntEnum):
    RIGHT = 0
    LEFT = 1
    BOTH = 2


@convertibleclass
class LegData:
    LEG_AFFECTED = "legAffected"
    SCORE = "score"

    pain: int = required_field(metadata=meta(validate_range(1, 5)))
    washing: int = required_field(metadata=meta(validate_range(1, 5)))
    transport: int = required_field(metadata=meta(validate_range(1, 5)))
    walk: int = required_field(metadata=meta(validate_range(1, 5)))
    meal: int = required_field(metadata=meta(validate_range(1, 5)))
    limping: int = required_field(metadata=meta(validate_range(1, 5)))
    kneelDown: int = required_field(metadata=meta(validate_range(1, 5)))
    bed: int = required_field(metadata=meta(validate_range(1, 5)))
    usualWork: int = required_field(metadata=meta(validate_range(1, 5)))
    letYouDown: int = required_field(metadata=meta(validate_range(1, 5)))
    shopping: int = required_field(metadata=meta(validate_range(1, 5)))
    stairs: int = required_field(metadata=meta(validate_range(1, 5)))
    score: int = field(default=0)
    legAffected: LegAffected = default_field()


@convertibleclass
class OxfordKneeScore(Primitive):
    LEG_AFFECTED = "legAffected"
    LEGS_DATA = "legsData"
    RIGHT_KNEE_SCORE = "rightKneeScore"
    LEFT_KNEE_SCORE = "leftKneeScore"

    legAffected: LegAffected = required_field()
    legsData: list[LegData] = required_field()
    rightKneeScore: int = default_field()
    leftKneeScore: int = default_field()
