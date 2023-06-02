from extensions.module_result.models.primitives import Primitive
from sdk.common.utils.convertible import required_field, meta, convertibleclass
from sdk.common.utils.validators import validate_range


@convertibleclass
class Tegner(Primitive):
    ACTIVITY_LEVEL_BEFORE = "activityLevelBefore"
    ACTIVITY_LEVEL_CURRENT = "activityLevelCurrent"

    activityLevelBefore: float = required_field(
        metadata=meta(value_to_field=float, validator=validate_range(0, 10))
    )
    activityLevelCurrent: float = required_field(
        metadata=meta(value_to_field=float, validator=validate_range(0, 10))
    )
