from mongoengine import StringField, EmbeddedDocumentField, EmbeddedDocumentListField

from extensions.deployment.models.econsent.econsent_section import EConsentSection
from extensions.deployment.repository.models.mongo_consent_model import (
    MongoConsent,
    MongoConsentSectionOptions,
    MongoConsentSection,
)
from sdk.common.common_models.mongo_models import MongoS3Object
from sdk.common.utils.enum_utils import enum_values


class MongoEConsentSectionOptions(MongoConsentSectionOptions):
    pass


class MongoEConsentSection(MongoConsentSection):
    type = StringField(choices=enum_values(EConsentSection.EConsentSectionType))
    contentType = StringField(choices=enum_values(EConsentSection.ContentType))
    thumbnailUrl = StringField()
    thumbnailLocation = EmbeddedDocumentField(MongoS3Object)
    videoUrl = StringField()
    videoLocation = EmbeddedDocumentField(MongoS3Object)


class MongoEConsent(MongoConsent):
    title = StringField()
    overviewTex = StringField()
    contactText = StringField()
    sections = EmbeddedDocumentListField(MongoEConsentSection)
