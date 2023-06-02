from datetime import datetime
from enum import Enum

from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    validate_id,
    default_datetime_meta,
    str_id_to_obj_id,
)


@convertibleclass
class HelperAgreementLog:
    class Status(Enum):
        DO_NOT_AGREE = "DO_NOT_AGREE"
        AGREE_AND_ACCEPT = "AGREE_AND_ACCEPT"

    ID = "id"
    USER_ID = "userId"
    DEPLOYMENT_ID = "deploymentId"
    STATUS = "status"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"

    id: str = default_field(metadata=meta(validate_id))
    userId: str = required_field(
        metadata=meta(
            validate_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )
    deploymentId: str = required_field(
        metadata=meta(
            validate_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )
    status: Status = required_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
