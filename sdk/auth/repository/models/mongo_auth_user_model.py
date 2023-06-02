from mongoengine import (
    ObjectIdField,
    DateTimeField,
    StringField,
    BooleanField,
    DictField,
    ListField,
    EmbeddedDocument,
    EmbeddedDocumentListField,
)

from sdk.auth.model.auth_user import AuthIdentifierType, AuthKey, AuthUser
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoAuthIdentifier(EmbeddedDocument):
    type = StringField(choices=enum_values(AuthIdentifierType))
    value = StringField()
    verified = BooleanField()


class MongoAuthKey(EmbeddedDocument):
    authKey = StringField()
    authIdentifier = StringField()
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
    active = BooleanField()
    authType = StringField(choices=enum_values(AuthKey.AuthType))


class MongoAuthUser(MongoPhoenixDocument):
    meta = {"collection": "authuser"}

    id = ObjectIdField()
    status = StringField(choices=enum_values(AuthUser.Status))
    emailVerified = BooleanField()
    email = StringField()
    phoneNumber = StringField()
    phoneNumberVerified = BooleanField()
    hashedPassword = StringField()
    previousPasswords = ListField(StringField)
    passwordCreateDateTime = DateTimeField()
    passwordUpdateDateTime = DateTimeField()
    mfaEnabled = BooleanField()
    displayName = StringField()
    validationData = DictField(default=None)
    userAttributes = DictField(default=None)
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
    mfaIdentifiers = EmbeddedDocumentListField(MongoAuthIdentifier)
    authKeys = EmbeddedDocumentListField(MongoAuthKey)
