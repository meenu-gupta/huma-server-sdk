from dataclasses import field

from extensions.module_result.models.primitives import Primitive
from sdk.common.utils.convertible import required_field, meta, convertibleclass
from sdk.common.utils.validators import validate_range


def lysholm_field():
    return required_field(
        metadata=meta(value_to_field=float, validator=validate_range(0, 25))
    )


@convertibleclass
class Lysholm(Primitive):
    LIMP = "limp"
    CANE_OR_CRUTCHES = "caneOrCrutches"
    LOCKING_SENSATION = "lockingSensation"
    GIVING_WAY_SENSATION = "givingWaySensation"
    PAIN = "pain"
    SWELLING = "swelling"
    CLIMBING_STAIRS = "climbingStairs"
    SQUATTING = "squatting"

    LYSHOLM = "lysholm"

    limp: float = lysholm_field()
    caneOrCrutches: float = lysholm_field()
    lockingSensation: float = lysholm_field()
    givingWaySensation: float = lysholm_field()
    pain: float = lysholm_field()
    swelling: float = lysholm_field()
    climbingStairs: float = lysholm_field()
    squatting: float = lysholm_field()

    # sum of all the other fields in this primitive
    lysholm: float = field(default=0, metadata=meta(value_to_field=float))
