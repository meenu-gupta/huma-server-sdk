from mongoengine import (
    ObjectIdField,
    DateTimeField,
    StringField,
    BooleanField,
    EmbeddedDocument,
    EmbeddedDocumentListField,
)

from extensions.identity_verification.models.identity_verification_log import (
    VerificationLog,
)
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class Document(EmbeddedDocument):
    id = ObjectIdField()
    isActive = BooleanField


class MongoVerificationLog(MongoPhoenixDocument):
    userId = ObjectIdField()
    deploymentId = ObjectIdField()
    applicantId = StringField()
    verificationStatus = StringField(choices=enum_values(VerificationLog.StatusType))
    verificationResult = StringField(choices=enum_values(VerificationLog.ResultType))
    checkId = StringField()
    legalFirstName = StringField()
    legalLastName = StringField()
    documents = EmbeddedDocumentListField(Document)
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
