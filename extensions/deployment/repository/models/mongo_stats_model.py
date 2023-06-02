from mongoengine import (
    EmbeddedDocument,
    IntField,
    StringField,
    EmbeddedDocumentField,
    DateTimeField,
)


class Stat(EmbeddedDocument):
    value = IntField()
    unit = StringField()


class MongoDeploymentStats(EmbeddedDocument):
    completedCount = EmbeddedDocumentField(Stat)
    completedTask = EmbeddedDocumentField(Stat)
    consentedCount = EmbeddedDocumentField(Stat)
    enrolledCount = EmbeddedDocumentField(Stat)
    patientCount = EmbeddedDocumentField(Stat)
    updateDateTime = DateTimeField()
