"""model for spirometry object"""

from sdk.common.utils.convertible import convertibleclass, meta, required_field
from .primitive import Primitive


@convertibleclass
class Spirometry(Primitive):
    """Spirometry model"""

    fvc: float = required_field(metadata=meta(value_to_field=float))
    fvcPredictedValue: float = required_field(metadata=meta(value_to_field=float))
    fev1: float = required_field(metadata=meta(value_to_field=float))
    fev1PredictedValue: float = required_field(metadata=meta(value_to_field=float))
