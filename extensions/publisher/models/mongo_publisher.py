from datetime import datetime

from mongoengine import (
    ObjectIdField,
    StringField,
    BooleanField,
    ListField,
    EmbeddedDocumentField,
    IntField,
    DateTimeField,
    EmbeddedDocument,
)

from extensions.publisher.models.mongo_gcp_fhir import MongoGCPFhir
from extensions.publisher.models.mongo_kafka import MongoKafka
from extensions.publisher.models.mongo_webhook import MongoWebhook
from extensions.publisher.models.publisher import Publisher
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoPublisher(MongoPhoenixDocument):
    meta = {
        "collection": "publisher",
        "indexes": [{"fields": [Publisher.PUBLISHER_NAME], "unique": True}],
    }

    class MongoPublisherTransform(EmbeddedDocument):
        deIdentified = BooleanField(default=False)
        includeNullFields = BooleanField(default=False)
        includeUserMetaData = BooleanField(default=False)
        excludeFields = ListField(StringField())
        includeFields = ListField(StringField())
        deIdentifyHashFields = ListField(StringField())
        deIdentifyRemoveFields = ListField(StringField())

    class MongoPublisherFilter(EmbeddedDocument):
        organizationIds = ListField(field=ObjectIdField())
        deploymentIds = ListField(field=ObjectIdField())
        moduleNames = ListField(StringField(), default=None)
        excludedModuleNames = ListField(StringField(), default=None)
        eventType = StringField(
            required=True,
            choices=enum_values(Publisher.Filter.EventType),
        )
        listenerType = StringField(
            required=True,
            choices=enum_values(Publisher.Filter.ListenerType),
        )

    class MongoPublisherTarget(EmbeddedDocument):
        retry = IntField(default=3)

        publisherType = StringField(
            required=True,
            choices=enum_values(Publisher.Target.Type),
        )

        webhook = EmbeddedDocumentField(MongoWebhook)
        kafka = EmbeddedDocumentField(MongoKafka)
        gcp_fhir = EmbeddedDocumentField(MongoGCPFhir)

    name = StringField(required=True)
    enabled = BooleanField(default=True)

    filter = EmbeddedDocumentField(MongoPublisherFilter)
    transform = EmbeddedDocumentField(MongoPublisherTransform)
    target = EmbeddedDocumentField(MongoPublisherTarget)

    updateDateTime = DateTimeField(default=datetime.utcnow)
    createDateTime = DateTimeField(default=datetime.utcnow)
