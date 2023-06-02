"""model for DailyCheckIn object"""
from enum import Enum

from sdk.common.utils.convertible import convertibleclass, required_field
from .primitive import Primitive


@convertibleclass
class Covid19DailyCheckIn(Primitive):
    """Daily check-in model"""

    CONTACT_TYPE = "contactType"

    class ContactTypeWithCovid19Person(Enum):
        I_LIVE_WITH_SUCH_PERSON = "I_LIVE_WITH_SUCH_PERSON"
        PROVIDED_DIRECT_CARE_TO_SUCH_A_PERSON = "PROVIDED_DIRECT_CARE_TO_SUCH_A_PERSON"
        DIRECT_PHYSICAL_CONTACT_WITH_SUCH_PERSON = (
            "DIRECT_PHYSICAL_CONTACT_WITH_SUCH_PERSON"
        )
        FACE_TO_FACE_CONTACT_WITH_SUCH_PERSON = "FACE_TO_FACE_CONTACT_WITH_SUCH_PERSON"
        NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"
        OTHER_TYPE_OF_CONTACT = "OTHER_TYPE_OF_CONTACT"

    contactType: ContactTypeWithCovid19Person = required_field()
