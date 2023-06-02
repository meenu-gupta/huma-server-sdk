from mongoengine import (
    EmbeddedDocument,
    ObjectIdField,
    DateTimeField,
    StringField,
    EmbeddedDocumentField,
    IntField,
    ListField,
    BooleanField,
    EmbeddedDocumentListField,
)

from extensions.deployment.models.consent.consent import AnswerFormat
from extensions.deployment.models.consent.consent_section import ConsentSection
from extensions.deployment.models.status import EnableStatus
from sdk.common.utils.enum_utils import enum_values


class MongoAdditionalConsentQuestion(EmbeddedDocument):
    type = StringField()
    enabled = StringField(choices=enum_values(EnableStatus))
    format = StringField(choices=enum_values(AnswerFormat))
    text = StringField()
    description = StringField()
    order = IntField()


class MongoConsentReview(EmbeddedDocument):
    title = StringField()
    details = StringField()


class MongoConsentSignature(EmbeddedDocument):
    signatureTitle = StringField()
    signatureDetails = StringField()
    nameTitle = StringField()
    nameDetails = StringField()
    hasMiddleName = BooleanField()
    showFirstLastName = BooleanField()


class MongoConsentSectionOptions(EmbeddedDocument):
    meta = {"allow_inheritance": True}

    type = IntField()
    text = StringField()
    order = IntField()
    abortOnChoose = BooleanField()


class MongoConsentSection(EmbeddedDocument):
    meta = {"allow_inheritance": True}

    type = StringField(choices=enum_values(ConsentSection.ConsentSectionType))
    title = StringField()
    details = StringField()
    reviewDetails = StringField()
    options = EmbeddedDocumentListField(MongoConsentSectionOptions)


class MongoConsent(EmbeddedDocument):
    meta = {"allow_inheritance": True}

    id = ObjectIdField()
    createDateTime = DateTimeField()
    enabled = StringField(choices=enum_values(EnableStatus))
    review = EmbeddedDocumentField(MongoConsentReview)
    revision = IntField()
    additionalConsentQuestions = ListField(
        EmbeddedDocumentField(MongoAdditionalConsentQuestion)
    )
    signature = EmbeddedDocumentField(MongoConsentSignature)
    sections = EmbeddedDocumentListField(MongoConsentSection)
    instituteName = StringField()
    instituteFullName = StringField()
    instituteTextDetails = StringField()
