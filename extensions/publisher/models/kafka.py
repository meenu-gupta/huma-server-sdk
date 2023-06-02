from enum import Enum

from sdk.common.utils.convertible import (
    convertibleclass,
    required_field,
    default_field,
)


@convertibleclass
class Kafka:
    class KafkaAuthType(Enum):
        SSL = "SSL"
        PLAIN = "PLAIN"

    url: str = required_field()
    topic: str = required_field(default="publisher_all")
    authType: KafkaAuthType = required_field(default=KafkaAuthType.PLAIN.value)
    saslUsername: str = default_field()
    saslPassword: str = default_field()
    tls: str = default_field()
