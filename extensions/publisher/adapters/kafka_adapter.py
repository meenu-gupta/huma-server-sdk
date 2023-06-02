import json
import logging
import uuid

from confluent_kafka import SerializingProducer

from extensions.common.monitoring import report_exception
from extensions.publisher.adapters.publisher_adapter import (
    PublisherAdapter,
    MODULE_ID,
    DEPLOYMENT_ID,
    DEVICE_NAME,
    MODULE_CONFIG_ID,
    PRIMITIVES,
)
from extensions.publisher.adapters.utils import transform_publisher_data
from extensions.publisher.models.publisher import Publisher
from sdk.common.utils.inject import autoparams

logger = logging.getLogger(__name__)


class KafkaAdapter(PublisherAdapter):
    @autoparams()
    def __init__(self, publisher: Publisher):
        self._publisher = publisher

    def transform_publisher_data(self, event: dict):
        transform_publisher_data(self._publisher, event)

    def prepare_publisher_data(self, event: dict) -> bool:
        self._headers = {"Content-Type": "application/json; charset=UTF-8"}

        self._message = {
            PRIMITIVES: event["primitives"],
            MODULE_ID: event["moduleId"],
            DEPLOYMENT_ID: event["deploymentId"],
            DEVICE_NAME: event["deviceName"],
            MODULE_CONFIG_ID: event["moduleConfigId"],
        }

        return True

    def send_publisher_data(self):
        server_url = self._publisher.target.kafka.url
        auth_type = self._publisher.target.kafka.authType
        sasl_username = self._publisher.target.kafka.saslUsername
        sasl_password = self._publisher.target.kafka.saslPassword

        if sasl_username and sasl_password:
            producer = SerializingProducer(
                {
                    "bootstrap.servers": server_url,
                    "sasl.mechanism": auth_type.value,
                    "security.protocol": "SASL_SSL",
                    "sasl.username": sasl_username,
                    "sasl.password": sasl_password,
                    "delivery.timeout.ms": 5000,
                }
            )
        else:
            report_exception(
                error=Exception("SASLUsername or SASLPassword is empty"),
                context_name="Publisher",
                context_content={
                    "publisherName": self._publisher.name,
                    "publisherType": self._publisher.target.publisherType,
                },
            )
            return

        self.send_data(producer)

    def send_data(self, producer):
        topic = self._publisher.target.kafka.topic

        def delivery_report(err, msg):
            if err:
                logger.debug("Message delivery failed: {}".format(err))

                report_exception(
                    error=Exception(err),
                    context_name="Publisher",
                    context_content={
                        "publisherName": self._publisher.name,
                        "publisherType": self._publisher.target.publisherType,
                    },
                )
            else:
                logger.debug(
                    "Message delivered to {} [{}]".format(msg.topic(), msg.partition())
                )

        key = uuid.uuid4()
        producer.produce(
            topic,
            key=str(key),
            value=json.dumps(self._message).encode("utf-8"),
            on_delivery=delivery_report,
        )
        producer.flush()

    def send_ping(self):
        self._headers = {"Content-Type": "application/json; charset=UTF-8"}
        self._message = {"ping": "pong"}

        self.send_publisher_data()
