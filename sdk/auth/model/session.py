from datetime import datetime

from sdk import meta, convertibleclass
from sdk.common.utils.convertible import default_field, field, required_field
from sdk.common.utils.validators import (
    validate_object_id,
    str_id_to_obj_id,
    default_datetime_meta,
)


@convertibleclass
class DeviceSession:
    ID = "id"
    ID_ = "_id"
    USER_ID = "userId"
    REFRESH_TOKEN = "refreshToken"
    DEVICE_AGENT = "deviceAgent"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"

    id: str = default_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    userId: str = default_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    refreshToken: str = default_field()
    deviceAgent: str = required_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())


@convertibleclass
class DeviceSessionV1:
    ID = "id"
    ID_ = "_id"
    USER_ID = "userId"
    REFRESH_TOKEN = "refreshToken"
    DEVICE_AGENT = "deviceAgent"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"
    IS_ACTIVE = "isActive"

    id: str = default_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    userId: str = default_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    refreshToken: str = default_field()
    deviceAgent: str = required_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    isActive: bool = field(default=True)
