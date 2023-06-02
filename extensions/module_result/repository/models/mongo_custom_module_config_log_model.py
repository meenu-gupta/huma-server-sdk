from mongoengine import (
    DateTimeField,
    DictField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
    IntField,
    ListField,
    ObjectIdField,
    StringField,
)

from extensions.deployment.models.status import EnableStatus
from extensions.deployment.repository.models.mongo_module_config_model import (
    MongoCustomRagThreshold,
    MongoFootnoteData,
    MongoModuleSchedule,
    MongoNotificationData,
    MongoStaticEvent,
)

from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoCustomModuleConfigLog(MongoPhoenixDocument):
    meta = {"collection": "custommoduleconfiglog"}

    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
    moduleId = StringField()
    moduleName = StringField()
    shortModuleName = StringField()
    status = StringField(choices=enum_values(EnableStatus))
    order = IntField()
    configBody = DictField(default=None)
    about = StringField()
    footnote = EmbeddedDocumentField(MongoFootnoteData)
    learnArticleIds = ListField(StringField(), default=None)
    version = IntField()
    customUnit = StringField()
    staticEvent = EmbeddedDocumentField(MongoStaticEvent)
    notificationData = EmbeddedDocumentField(MongoNotificationData)
    localizationPrefix = StringField()
    ragThresholds = EmbeddedDocumentListField(MongoCustomRagThreshold, default=None)
    reason = StringField()
    schedule = EmbeddedDocumentField(MongoModuleSchedule)
    userId = ObjectIdField()
    clinicianId = ObjectIdField()
    moduleConfigId = ObjectIdField()
