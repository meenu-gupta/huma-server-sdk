from sdk import convertibleclass
from sdk.common.utils.convertible import meta, required_field
from sdk.common.utils.validators import (
    validate_range,
)
from enum import Enum


MAX_SIZE_VALUE = 10


def _validate_size(size: str):
    split_values = size.split("x")
    if len(split_values) != 2:
        return False
    for value in split_values:
        try:
            if not MAX_SIZE_VALUE >= int(value) >= 1:
                return False
        except ValueError:
            return False
    return True


class GadgetId(Enum):
    SIGNED_UP = "SignedUp"
    CONSENTED = "Consented"
    KEY_METRICS = "KeyMetrics"
    OVERALL_VIEW = "OverallView"
    DEPLOYMENT_OVERVIEW = "DeploymentOverview"
    STUDY_PROGRESS = "StudyProgress"


@convertibleclass
class GadgetLink:
    ID = "id"
    SIZE = "size"
    ORDER = "order"

    id: GadgetId = required_field()
    order: int = required_field(metadata=meta(validator=validate_range(min_=1)))
    size: str = required_field(metadata=meta(validator=_validate_size))
