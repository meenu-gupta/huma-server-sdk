from dataclasses import field

from sdk.common.utils.convertible import convertibleclass, meta, required_field
from sdk.common.utils.validators import validate_object_id
from sdk.inbox.models.message import Message


@convertibleclass
class MessageSearchRequestObject:
    USER_ID = "userId"
    SUBMITTER_ID = "submitterId"
    SKIP = "skip"
    LIMIT = "limit"
    CUSTOM = "custom"

    userId: str = required_field(metadata=meta(validate_object_id))
    submitterId: str = required_field(metadata=meta(validate_object_id))
    skip: int = required_field()
    limit: int = required_field()
    custom: bool = field(default=False)


@convertibleclass
class MessageSearchResponseObject:
    MESSAGES = "messages"

    messages: list[Message] = required_field()
