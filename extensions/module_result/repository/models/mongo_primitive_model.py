from sdk.common.utils.mongo_utils import MongoPhoenixDocument
from mongoengine import (
    ObjectIdField,
    DateTimeField,
    StringField,
    BooleanField,
    DictField,
    IntField,
    EmbeddedDocument,
    EmbeddedDocumentField,
)


class MongoServerObject(EmbeddedDocument):
    hostUrl = StringField()
    server = StringField()
    api = StringField()


class MongoUserAgentObject(EmbeddedDocument):
    product = StringField()
    version = StringField()
    software_name = StringField()
    software_version = StringField()
    bundle_id = StringField()
    build = StringField()
    hardware = StringField()
    component = StringField()
    language = StringField()


class MongoPrimitive(MongoPhoenixDocument):
    id = ObjectIdField()
    userId = ObjectIdField()
    moduleId = StringField()
    moduleConfigId = StringField()
    deploymentId = ObjectIdField()
    version = IntField()
    deviceName = StringField()
    deviceDetails = StringField()
    isAggregated = BooleanField()
    aggregationPrecision = StringField()
    startDateTime = DateTimeField()
    endDateTime = DateTimeField()
    createDateTime = DateTimeField()
    submitterId = ObjectIdField()
    correlationStartDateTime = DateTimeField()
    tags = DictField(default=None)
    tagsAuthorId = ObjectIdField()
    client = EmbeddedDocumentField(MongoUserAgentObject)
    server = EmbeddedDocumentField(MongoServerObject)
