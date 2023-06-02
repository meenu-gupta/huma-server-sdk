from datetime import datetime

from mongoengine import ObjectIdField, DictField, DateTimeField

from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoTagLog(MongoPhoenixDocument):
    meta = {"collection": "taglog", "indexes": ["userId", "authorId"]}

    userId = ObjectIdField(required=True)
    authorId = ObjectIdField(required=True)
    tags = DictField(required=True)
    createDateTime = DateTimeField(default=datetime.utcnow)
