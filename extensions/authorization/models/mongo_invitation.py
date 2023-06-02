from datetime import datetime

from mongoengine import (
    EmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    DictField,
)
from mongoengine import ObjectIdField, StringField, ListField, DateTimeField

from extensions.authorization.models.invitation import Invitation, InvitationType
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoRoleAssignmentObject(EmbeddedDocument):
    roleId = StringField(required=True)
    resource = StringField(required=True)
    userType = StringField()


class MongoInvitation(MongoPhoenixDocument):
    meta = {
        "collection": "invitation",
        "indexes": [
            {"fields": [Invitation.EXPIRES_AT], "expireAfterSeconds": 0, "cls": False},
        ],
    }

    EXPIRES_AT = "expiresAt"

    email = StringField()
    code = StringField(required=True)
    shortenedCode = StringField(unique=True, required=False, sparse=True, null=True)
    roles = ListField(EmbeddedDocumentField(MongoRoleAssignmentObject))
    numberOfTry = IntField(default=1)
    type = StringField(choices=enum_values(InvitationType))
    expiresAt = DateTimeField(required=True)
    createDateTime = DateTimeField(default=datetime.utcnow)
    senderId = ObjectIdField()
    clientId = StringField()
    extraInfo = DictField()
