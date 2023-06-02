from extensions.twilio_video.models.twilio_video import VideoCall
from sdk import convertibleclass, meta
from sdk.common.utils.convertible import (
    required_field,
    positive_integer_field,
    natural_number_field,
    default_field,
)
from sdk.common.utils.validators import (
    validate_entity_name,
    validate_object_id,
)

DEFAULT_CALLS_RESULT_PAGE_SIZE = 20


@convertibleclass
class StartVideoCallRequestObject:
    USER_ID = "userId"
    MANAGER_ID = "managerId"

    userId: str = required_field(metadata=meta(validate_object_id))
    managerId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class CompleteVideoCallRequestObject:
    CALL_ID = "callId"

    token: str = required_field()
    callId: str = required_field(metadata=meta(validate_entity_name))


@convertibleclass
class RetrieveCallsRequestObject:
    SKIP = "skip"
    LIMIT = "limit"
    REQUESTER_ID = "requesterId"
    USER_ID = "userId"
    VIDEO_CALL_ID = "video_call_id"

    skip: int = positive_integer_field(default=0)
    limit: int = natural_number_field(default=DEFAULT_CALLS_RESULT_PAGE_SIZE)
    requesterId: str = required_field(metadata=meta(validate_object_id))
    userId: str = required_field(metadata=meta(validate_object_id))
    video_call_id: str = default_field()


@convertibleclass
class InitiateVideoCallRequestObject:
    APPOINTMENT_ID = "appointmentId"

    appointmentId: str = default_field(metadata=meta(validate_object_id))


@convertibleclass
class CompleteUserVideoCallRequestObject:
    REASON = "reason"

    reason: VideoCall.CallStatus = default_field()
