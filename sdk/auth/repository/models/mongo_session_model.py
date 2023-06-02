from mongoengine import BooleanField, ObjectIdField, StringField, DateTimeField

from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoDeviceSession(MongoPhoenixDocument):
    meta = {"collection": "devicesession"}

    id = ObjectIdField()
    userId = ObjectIdField()
    refreshToken = StringField()
    deviceAgent = StringField()
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
    isActive = BooleanField()
