from dataclasses import field

from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
)
from sdk.common.utils.validators import validate_object_id, must_not_be_empty_list, not_empty


@convertibleclass
class SendMessageToPatientListRequestObject:
    TEXT = "text"
    CUSTOM = "custom"
    USER_IDS = "userIds"
    ALL_USERS = "allUsers"
    SUBMITTER_ID = "submitterId"
    SUBMITTER_NAME = "submitterName"

    text: str = required_field()
    custom: bool = field(default=False)
    userIds: list[str] = required_field(
        metadata=meta(lambda x: all(map(validate_object_id, x)))
    )
    allUsers: bool = field(default=False)
    submitterId: str = required_field(metadata=meta(validate_object_id))
    submitterName: str = required_field(metadata=meta(not_empty))

    @classmethod
    def validate(cls, request_object):
        if not request_object.allUsers:
            must_not_be_empty_list(userIds=request_object.userIds)
