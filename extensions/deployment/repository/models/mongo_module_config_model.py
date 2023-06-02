from mongoengine import (
    EmbeddedDocument,
    ObjectIdField,
    DateTimeField,
    StringField,
    FloatField,
    IntField,
    DictField,
    EmbeddedDocumentField,
    ListField,
    BooleanField,
    EmbeddedDocumentListField,
)

from extensions.deployment.models.status import EnableStatus
from extensions.module_result.models.module_config import (
    RagThresholdType,
    TimeOfDay,
    Weekday,
)
from sdk.common.utils.enum_utils import enum_values


class MongoModuleSchedule(EmbeddedDocument):
    isoDuration = StringField()
    timesPerDuration = IntField()
    friendlyText = StringField()
    timesOfDay = ListField(StringField(choices=enum_values(TimeOfDay)), default=None)
    timesOfReadings = ListField(StringField(), default=None)
    specificWeekDays = ListField(
        StringField(choices=enum_values(Weekday)), default=None
    )


class MongoStaticEvent(EmbeddedDocument):
    enabled = BooleanField()
    isoDuration = StringField()
    title = StringField()
    description = StringField()


class MongoNotificationData(EmbeddedDocument):
    title = StringField()
    body = StringField()


class MongoFootnoteData(EmbeddedDocument):
    enabled = BooleanField()
    text = StringField()


class MongoThresholdRange(EmbeddedDocument):
    minValue = FloatField()
    maxValue = FloatField()
    exactValueStr = StringField()


class MongoRagThreshold(EmbeddedDocument):
    meta = {"allow_inheritance": True}

    type = StringField(choices=enum_values(RagThresholdType))
    severity = IntField()
    thresholdRange = EmbeddedDocumentListField(MongoThresholdRange)
    color = StringField()
    fieldName = StringField()
    enabled = BooleanField()


class MongoCustomRagThreshold(MongoRagThreshold):
    isCustom = BooleanField()


class MongoModuleConfig(EmbeddedDocument):
    meta = {"allow_inheritance": True}

    id = ObjectIdField()
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
    moduleId = StringField()
    moduleName = StringField()
    shortModuleName = StringField()
    status = StringField(choices=enum_values(EnableStatus))
    order = IntField()
    configBody = DictField()
    about = StringField()
    footnote = EmbeddedDocumentField(MongoFootnoteData)
    schedule = EmbeddedDocumentField(MongoModuleSchedule)
    ragThresholds = EmbeddedDocumentListField(MongoRagThreshold)
    learnArticleIds = ListField(StringField())
    version = IntField()
    customUnit = StringField()
    staticEvent = EmbeddedDocumentField(MongoStaticEvent)
    notificationData = EmbeddedDocumentField(MongoNotificationData)
    localizationPrefix = StringField()
