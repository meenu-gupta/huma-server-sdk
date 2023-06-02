from datetime import datetime

from mongoengine import (
    StringField,
    BooleanField,
    DateTimeField,
    ObjectIdField,
    DictField,
    ReferenceField,
    ListField,
)

from sdk.common.exceptions.exceptions import ClassNotRegisteredException
from sdk.common.utils.mongo_utils import MongoPhoenixDocument

_mongo_cls = {}


class MongoCalendarEvent(MongoPhoenixDocument):
    meta = {"collection": "calendar", "allow_inheritance": True}

    USER_ID = "userId"

    model = StringField(required=True)
    title = StringField()
    description = StringField()
    userId = ObjectIdField(required=True)
    enabled = BooleanField(default=True)
    isRecurring = BooleanField()
    recurrencePattern = StringField()
    instanceExpiresIn = StringField()
    startDateTime = DateTimeField()
    endDateTime = DateTimeField()
    extraFields = DictField()
    snoozing = ListField(StringField())
    parentId = ObjectIdField()
    updateDateTime = DateTimeField(default=datetime.utcnow)
    createDateTime = DateTimeField(default=datetime.utcnow)
    language = StringField()
    completeDateTime = DateTimeField()

    @classmethod
    def child(cls, name):
        if name not in _mongo_cls:
            raise ClassNotRegisteredException
        return _mongo_cls[name]

    @staticmethod
    def clear(name: str = None):
        global _mongo_cls
        if name and name in _mongo_cls:
            del _mongo_cls[name]
        else:
            _mongo_cls = {}

    @classmethod
    def register(cls, name, sub_class):
        _mongo_cls[name] = sub_class

    @staticmethod
    def reminders():
        return _mongo_cls


class MongoCalendarEventLog(MongoPhoenixDocument):
    meta = {"collection": "calendarlog"}

    USER_ID = "userId"

    model = StringField(required=True)
    userId = ObjectIdField()
    parentId = ReferenceField(MongoCalendarEvent)
    startDateTime = DateTimeField(required=True)
    endDateTime = DateTimeField(required=True)
    updateDateTime = DateTimeField(default=datetime.utcnow)
    createDateTime = DateTimeField(default=datetime.utcnow)
