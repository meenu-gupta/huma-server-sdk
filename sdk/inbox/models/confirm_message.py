from sdk.common.utils.convertible import convertibleclass, required_field, meta
from sdk.common.utils.validators import validate_object_ids


@convertibleclass
class ConfirmMessageRequestObject:
    MESSAGE_IDS = "messageIds"

    messageIds: list[str] = required_field(metadata=meta(validate_object_ids))


@convertibleclass
class ConfirmMessageResponseObject:
    UPDATED = "updated"

    updated: int = required_field()
