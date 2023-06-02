from datetime import datetime

from sdk.common.utils.convertible import (
    convertibleclass,
    required_field,
    default_field,
)
from sdk.common.utils.validators import default_datetime_meta


@convertibleclass
class IdentityVerificationSdkTokenResponse:
    APPLICANT_ID = "applicantId"
    TOKEN = "token"
    UTC_EXPIRATION_DATE_TIME = "utcExpirationDateTime"

    applicantId: str = required_field()
    token: str = required_field()
    utcExpirationDateTime: datetime = default_field(metadata=default_datetime_meta())
