from mongoengine import (
    EmbeddedDocument,
    StringField,
    BooleanField,
    IntField,
    ObjectIdField,
    DynamicField,
    EmbeddedDocumentListField,
)

from extensions.deployment.models.care_plan_group import (
    ModuleConfigPatch,
    OperationType,
)
from sdk.common.utils.enum_utils import enum_values


class MongoPatch(EmbeddedDocument):
    op = StringField(choices=enum_values(OperationType))
    path = StringField()
    value = DynamicField()


class MongoModuleConfigPatch(EmbeddedDocument):
    moduleConfigId = ObjectIdField()
    changeType = StringField(choices=enum_values(ModuleConfigPatch.ChangeType))
    patch = EmbeddedDocumentListField(MongoPatch)


class MongoGroup(EmbeddedDocument):
    id = StringField()
    name = StringField()
    moduleConfigPatches = EmbeddedDocumentListField(MongoModuleConfigPatch)
    default = BooleanField()
    extensionForActivationCode = StringField()
    order = IntField()


class MongoCarePlanGroup(EmbeddedDocument):
    groups = EmbeddedDocumentListField(MongoGroup)
