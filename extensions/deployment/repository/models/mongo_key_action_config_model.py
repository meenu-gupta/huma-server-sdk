from mongoengine import (
    DateTimeField,
    ObjectIdField,
    StringField,
    IntField,
    EmbeddedDocument,
)

from extensions.deployment.models.key_action_config import KeyActionConfig
from sdk.common.utils.enum_utils import enum_values


class MongoKeyActionConfig(EmbeddedDocument):

    id = ObjectIdField()
    title = StringField()
    description = StringField()
    deltaFromTriggerTime = StringField()
    durationFromTrigger = StringField()
    durationIso = StringField()
    instanceExpiresIn = StringField()
    type = StringField(choices=enum_values(KeyActionConfig.Type))
    trigger = StringField(choices=enum_values(KeyActionConfig.Trigger))
    notifyEvery = StringField()
    numberOfNotifications = IntField()

    learnArticleId = ObjectIdField()
    moduleId = StringField()
    moduleConfigId = ObjectIdField()

    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
