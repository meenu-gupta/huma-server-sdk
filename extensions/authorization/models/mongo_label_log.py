from datetime import datetime

from mongoengine import ObjectIdField, DateTimeField

from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoLabelLog(MongoPhoenixDocument):
    meta = {"collection": "labellog", "indexes": ["userId", "assigneeId"]}

    userId = ObjectIdField(required=True)
    assigneeId = ObjectIdField(required=True)
    labelId = ObjectIdField(required=True)
    createDateTime = DateTimeField(default=datetime.utcnow)
