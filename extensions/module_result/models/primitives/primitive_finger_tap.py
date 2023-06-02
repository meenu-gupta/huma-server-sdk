"""model for finger tap object"""
from sdk.common.utils.convertible import convertibleclass, meta, default_field
from .primitive import Primitive


@convertibleclass
class FingerTap(Primitive):
    """FingerTap model"""

    leftHandValue: int = default_field(metadata=meta(int, True))
    rightHandValue: int = default_field(metadata=meta(int, True))
