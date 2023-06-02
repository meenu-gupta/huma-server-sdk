from mongoengine import StringField, EmbeddedDocument

from extensions.publisher.models.kafka import Kafka
from sdk.common.utils.enum_utils import enum_values


class MongoKafka(EmbeddedDocument):

    url = StringField()
    topic = StringField()
    authType = StringField(
        choices=enum_values(Kafka.KafkaAuthType),
        default=Kafka.KafkaAuthType.PLAIN.value,
    )
    saslUsername = StringField()
    saslPassword = StringField()
    tls = StringField()
