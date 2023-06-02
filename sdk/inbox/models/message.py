from dataclasses import field
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


class MessageStatusType(Enum):
    DELIVERED = "DELIVERED"
    READ = "READ"


@convertibleclass
class Message:
    ID = "id"
    USER_ID = "userId"
    SUBMITTER_ID = "submitterId"
    SUBMITTER_NAME = "submitterName"
    TEXT = "text"
    STATUS = "status"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"
    CUSTOM = "custom"

    id: str = default_field(metadata=meta(validate_id))
    userId: str = required_field()
    submitterId: str = required_field()
    submitterName: str = default_field()
    text: str = required_field(metadata=meta(validate_len(1, 280)))
    status: MessageStatusType = default_field()
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    custom: bool = field(default=False)


@convertibleclass
class SubmitterMessageReport:
    LATEST_MESSAGE = "latestMessage"
    UNREAD_MESSAGE_COUNT = "unreadMessageCount"
    CUSTOM = "custom"

    latestMessage: Message = default_field()
    unreadMessageCount: int = default_field()
    custom: bool = field(default=False)

    def post_init(self):
        if self.latestMessage.custom:
            self.custom = True
