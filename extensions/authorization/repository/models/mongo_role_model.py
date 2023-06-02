from mongoengine import EmbeddedDocument, ObjectIdField, StringField

from extensions.authorization.models.role.default_permissions import PermissionType
from sdk.common.utils.enum_utils import enum_values


class MongoRole(EmbeddedDocument):
    id = ObjectIdField()
    name = StringField()
    permissions = StringField(choices=enum_values(PermissionType))
    userType = StringField()
