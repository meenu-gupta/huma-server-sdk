"""model for AwarenessTraining object"""
from sdk.common.utils.convertible import convertibleclass, default_field
from .primitive import Primitive


@convertibleclass
class AwarenessTraining(Primitive):
    """AwarenessTraining model"""

    certificateNumber: str = default_field()
    # calculated result
    totalHealthScore: int = default_field()
    # HIGH MODERATE LOW
    status: str = default_field()
