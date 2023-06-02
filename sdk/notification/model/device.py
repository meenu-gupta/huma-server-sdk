from datetime import datetime
from enum import Enum

from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    validate_id,
    default_datetime_meta,
    validate_len,
)


class PushIdType(Enum):
    TWILIO = "TWILIO"
    ANDROID_FCM = "ANDROID_FCM"
    IOS_APNS = "IOS_APNS"
    IOS_VOIP = "IOS_VOIP"
    ALI_CLOUD = "ALI_CLOUD"


@convertibleclass
class Device:
    ID = "id"
    USER_ID = "userId"
    DEVICE_PUSH_ID = "devicePushId"
    DEVICE_PUSH_ID_TYPE = "devicePushIdType"
    DEVICE_DETAILS = "deviceDetails"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"

    id: str = default_field(metadata=meta(validate_id))
    userId: str = default_field()
    devicePushId: str = required_field(metadata=meta(validate_len(min=1)))
    devicePushIdType: PushIdType = required_field()
    deviceDetails: str = default_field()
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
