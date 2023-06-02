from enum import Enum

from sdk import convertibleclass, meta
from sdk.common.utils.convertible import default_field
from sdk.common.utils.validators import validate_object_id, validate_datetime


@convertibleclass
class VideoCallLog:
    EVENT = "event"
    IDENTITY = "identity"

    class EventType(Enum):
        USER_JOINED = "participant-connected"
        USER_LEFT = "participant-disconnected"
        ROOM_CREATED = "room-created"
        ROOM_FINISHED = "room-ended"

    id: str = default_field(metadata=meta(validate_object_id))
    event: str = default_field()
    identity: str = default_field()
    createDateTime: str = default_field(metadata=meta(validate_datetime))


@convertibleclass
class VideoCall:
    MANAGER_ID = "managerId"
    USER_ID = "userId"
    START_DATE_TIME = "startDateTime"
    END_DATE_TIME = "endDateTime"
    LOGS = "logs"
    TYPE = "type"

    class TwilioRoomStatus(Enum):
        IN_PROGRESS = "in-progress"
        COMPLETED = "completed"
        FAILED = "failed"

    class CallType(Enum):
        SCHEDULED = "SCHEDULED"
        UNSCHEDULED = "UNSCHEDULED"

    class CallStatus(Enum):
        MISSED = "MISSED"
        ANSWERED = "ANSWERED"
        DECLINED = "DECLINED"

    id: str = default_field(metadata=meta(validate_object_id))
    managerId: str = default_field(metadata=meta(validate_object_id))
    userId: str = default_field(metadata=meta(validate_object_id))
    duration: int = default_field()
    startDateTime: str = default_field(metadata=meta(validate_datetime))
    endDateTime: str = default_field(metadata=meta(validate_datetime))
    updateDateTime: str = default_field(metadata=meta(validate_datetime))
    createDateTime: str = default_field(metadata=meta(validate_datetime))
    roomStatus: str = default_field()
    logs: list[VideoCallLog] = default_field()
    appointmentId: str = default_field(metadata=meta(validate_object_id))
    type: CallType = default_field()
    status: CallStatus = default_field()

    def post_init(self):
        self.type = (
            VideoCall.CallType.SCHEDULED
            if self.appointmentId
            else VideoCall.CallType.UNSCHEDULED
        )


class VideoAction(Enum):
    InitiateVideoCall = "InitiateVideoCall"
    CompleteVideoCallManager = "CompleteVideoCallManager"
    CompleteVideoCallUser = "CompleteVideoCallUser"
