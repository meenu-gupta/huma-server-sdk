from mongoengine import (
    ObjectIdField,
    StringField,
    ListField,
    IntField,
    DateTimeField,
    EmbeddedDocumentListField,
)

from extensions.authorization.repository.models.mongo_role_model import MongoRole
from extensions.deployment.models.status import Status
from extensions.organization.models.organization import Organization
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoOrganization(MongoPhoenixDocument):
    meta = {"collection": "organization"}

    id = ObjectIdField()
    name = StringField()
    status = StringField(choices=enum_values(Status))
    deploymentIds = ListField(StringField)
    enrollmentTarget = IntField()
    studyCompletionTarget = IntField()
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
    privacyPolicyUrl = StringField()
    eulaUrl = StringField()
    termAndConditionUrl = StringField()
    viewType = StringField(choices=enum_values(Organization.ViewType))
    roles = EmbeddedDocumentListField(MongoRole)
