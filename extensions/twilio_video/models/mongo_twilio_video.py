from datetime import datetime

from mongoengine import (
    ObjectIdField,
    StringField,
    DateTimeField,
    IntField,
    EmbeddedDocumentField,
    EmbeddedDocument,
    ListField,
)

from extensions.twilio_video.models.twilio_video import VideoCall, VideoCallLog
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoVideoCallLog(EmbeddedDocument):
    TYPE_CHOICES = [item.value for item in VideoCallLog.EventType]
    event = StringField(
        required=True,
        choices=TYPE_CHOICES,
        default=VideoCall.TwilioRoomStatus.IN_PROGRESS.value,
    )
    identity = StringField(required=False)
    createDateTime = DateTimeField(default=datetime.utcnow)


class MongoVideoCall(MongoPhoenixDocument):
    meta = {"collection": "video_call"}

    STATUS_CHOICES = [item.value for item in VideoCall.TwilioRoomStatus]
    USER_ID = "userId"

    userId = ObjectIdField(required=True)
    managerId = ObjectIdField(required=True)
    roomStatus = StringField(
        required=True,
        choices=STATUS_CHOICES,
        default=VideoCall.TwilioRoomStatus.IN_PROGRESS.value,
    )
    startDateTime = DateTimeField()
    endDateTime = DateTimeField()
    updateDateTime = DateTimeField(default=datetime.utcnow)
    createDateTime = DateTimeField(default=datetime.utcnow)
    duration = IntField(default=0)
    logs = ListField(EmbeddedDocumentField(MongoVideoCallLog))
    appointmentId = ObjectIdField(default=None)
    status = StringField(default=None)
