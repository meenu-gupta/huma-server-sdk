from datetime import datetime
from dataclasses import field
from enum import Enum

from extensions.export_deployment.models.export_deployment_models import (
    DEFAULT_EXCLUDE_FIELDS,
    DEFAULT_DEIDENTIFY_HASH_FIELDS,
    DEFAULT_DEIDENTIFY_REMOVE_FIELDS,
)
from extensions.publisher.models.gcp_fhir import GCPFhir
from extensions.publisher.models.kafka import Kafka
from extensions.publisher.models.webhook import Webhook
from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    validate_object_id,
    validate_object_ids,
    validate_entity_name,
    default_datetime_meta,
)


@convertibleclass
class Publisher:
    """Publisher model for sending data to the outside world"""

    ID = "id"
    ID_ = "_id"

    PUBLISHER_TRANSFORM = "transform"
    PUBLISHER_TARGET = "target"
    PUBLISHER_FILTER = "filter"
    PUBLISHER_NAME = "name"
    PUBLISHER_TYPE = "publisherType"
    EVENT_TYPE = "eventType"
    LISTENER_TYPE = "listenerType"
    RETRY = "retry"
    INCLUDE_NULL_FIELDS = "includeNullFields"
    INCLUDE_USER_META_DATA = "includeUserMetaData"
    DEIDENTIFIED = "deIdentified"
    DEPLOYMENT_IDS = "deploymentIds"
    ORGANIZATION_IDS = "organizationIds"
    USE_FLAT_STRUCTURE = "useFlatStructure"
    EXCLUDE_FIELDS = "excludeFields"
    INCLUDE_FIELDS = "includeFields"
    MODULE_NAMES = "moduleNames"
    ENABLED = "enabled"
    KAFKA = "kafka"
    WEBHOOK = "webhook"
    GCPFHIR = "gcp_fhir"

    @convertibleclass
    class Filter:
        class EventType(Enum):
            PING = "PING"
            MODULE_RESULT = "MODULE_RESULT"

        class ListenerType(Enum):
            DEPLOYMENT_IDS = "DEPLOYMENT_IDS"
            ORGANIZATION_IDS = "ORGANIZATION_IDS"
            GLOBAL = "GLOBAL"

        eventType: EventType = required_field()
        listenerType: ListenerType = required_field()
        organizationIds: list[str] = default_field(metadata=meta(validate_object_ids))
        deploymentIds: list[str] = default_field(metadata=meta(validate_object_ids))
        moduleNames: list[str] = default_field()
        excludedModuleNames: list[str] = default_field()

    @convertibleclass
    class Transform:
        deIdentified: bool = field(default=False)
        includeNullFields: bool = field(default=True)
        includeUserMetaData: bool = field(default=True)
        includeFields: list[str] = default_field()
        excludeFields: list[str] = field(default=DEFAULT_EXCLUDE_FIELDS)
        deIdentifyHashFields: list[str] = field(default=DEFAULT_DEIDENTIFY_HASH_FIELDS)
        deIdentifyRemoveFields: list[str] = field(
            default=DEFAULT_DEIDENTIFY_REMOVE_FIELDS
        )

    @convertibleclass
    class Target:
        class Type(Enum):
            WEBHOOK = "WEBHOOK"
            KAFKA = "KAFKA"
            GCPFHIR = "GCPFHIR"

        retry: int = field(default=3)
        publisherType: Type = required_field()
        webhook: Webhook = default_field()
        kafka: Kafka = default_field()
        gcp_fhir: GCPFhir = default_field()

    id: str = default_field(metadata=meta(validate_object_id))

    name: str = required_field(metadata=meta(validator=validate_entity_name))
    enabled: bool = field(default=True)

    filter: Filter = required_field()
    transform: Transform = required_field()
    target: Target = required_field()

    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())


class PublisherAction(Enum):
    CreatePublisher = "CreatePublisher"
    UpdatePublisher = "UpdatePublisher"
    RetrievePublisher = "RetrievePublisher"
    RetrievePublishers = "RetrievePublishers"
    DeletePublisher = "DeletePublisher"
