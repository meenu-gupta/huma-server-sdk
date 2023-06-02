from mongoengine import (
    StringField,
    EmbeddedDocumentField,
    DateTimeField,
    ListField,
    ObjectIdField,
    EmbeddedDocument,
    EmbeddedDocumentListField,
)

from extensions.module_result.repository.models import MongoPrimitive
from extensions.revere.models.revere import RevereTest
from sdk.common.common_models.mongo_models import MongoS3Object
from sdk.common.utils.enum_utils import enum_values


class MongoRevereTestResult(EmbeddedDocument):
    initialWords = ListField(StringField())
    audioResult = EmbeddedDocumentField(MongoS3Object)
    wordsResult = ListField(StringField())
    inputLanguageIETFTag = StringField()
    buildNumber = StringField()


class MongoRevereTest(MongoPrimitive):
    meta = {"collection": "reveretest"}

    id = ObjectIdField()
    userId = ObjectIdField()
    startDateTime = DateTimeField()
    endDateTime = DateTimeField()
    results = EmbeddedDocumentListField(MongoRevereTestResult)
    status = StringField(choices=enum_values(RevereTest.Status))
    moduleId = StringField()
    deploymentId = ObjectIdField()
