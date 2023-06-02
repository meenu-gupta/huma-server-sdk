from datetime import datetime

from mongoengine import ObjectIdField, StringField, DateTimeField, BooleanField

from sdk.common.utils.mongo_utils import MongoPhoenixDocument
from sdk.inbox.models.message import Message, MessageStatusType


class MongoMessageDocument(MongoPhoenixDocument):
    INBOX_COLLECTION = "inbox"

    STATUS_TYPE_CHOICES = [item.value for item in MessageStatusType]
    USER_ID = "userId"
    SUBMITTER_ID = "submitterId"
    SUBMITTER_NAME = "submitterName"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"
    TEXT = "text"
    STATUS = "status"
    CUSTOM = "custom"

    meta = {"collection": INBOX_COLLECTION, "indexes": [USER_ID, SUBMITTER_ID]}

    userId = ObjectIdField(required=True)
    submitterId = ObjectIdField(required=True)
    submitterName = StringField()
    text = StringField(required=True)
    status = StringField(
        choices=STATUS_TYPE_CHOICES, default=MessageStatusType.DELIVERED
    )
    updateDateTime = DateTimeField(default=datetime.utcnow)
    createDateTime = DateTimeField(default=datetime.utcnow)
    custom = BooleanField()
