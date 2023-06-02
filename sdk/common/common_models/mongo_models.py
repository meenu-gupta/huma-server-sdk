from mongoengine import (
    EmbeddedDocument,
    StringField,
)


class MongoS3Object(EmbeddedDocument):
    bucket = StringField(required=True)
    key = StringField(required=True)
    region = StringField(required=True)
