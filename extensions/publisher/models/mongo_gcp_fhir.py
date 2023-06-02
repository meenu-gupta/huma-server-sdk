from mongoengine import EmbeddedDocument, URLField, StringField, DictField


class MongoGCPFhir(EmbeddedDocument):
    url = URLField()
    serviceAccountData: str = StringField()
    config: dict = DictField()
