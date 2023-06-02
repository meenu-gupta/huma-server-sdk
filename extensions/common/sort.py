from enum import Enum

from sdk.common.utils.convertible import convertibleclass, required_field


@convertibleclass
class SortField:
    FIELD = "field"
    DIRECTION = "direction"

    class Direction(Enum):
        ASC = "ASC"
        DESC = "DESC"

    field: str = required_field()
    direction: Direction = required_field()
