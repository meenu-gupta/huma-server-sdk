"""model for user action object"""
from enum import Enum

from sdk.common.utils.convertible import convertibleclass, required_field
from .primitive import Primitive


@convertibleclass
class UserAction(Primitive):
    """UserAction model"""

    class Action(Enum):
        RETAKE = "RETAKE"
        CONFIRM = "CONFIRM"

    action: Action = required_field()
