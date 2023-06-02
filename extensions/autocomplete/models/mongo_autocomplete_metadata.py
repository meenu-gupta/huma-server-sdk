from datetime import datetime

from mongoengine import EmbeddedDocumentField, StringField, DateTimeField

from sdk.common.common_models.mongo_models import MongoS3Object
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoAutoCompleteMetadata(MongoPhoenixDocument):
    meta = {"collection": "autocomplete"}

    s3Object = EmbeddedDocumentField(MongoS3Object)
    moduleId = StringField()
    language = StringField()
    updateDateTime = DateTimeField(default=datetime.utcnow)
