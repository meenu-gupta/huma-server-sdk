import copy
import logging

from extensions.export_deployment.helpers.convertion_helpers import (
    get_primitive_dict,
)
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.publisher.adapters.gcp_fhir_adapter import GCPFHIRAdapter
from extensions.publisher.adapters.kafka_adapter import KafkaAdapter
from extensions.publisher.adapters.webhook_adapter import WebhookAdapter
from extensions.publisher.models.primitive_data import PrimitiveData
from extensions.publisher.models.publisher import Publisher
from extensions.publisher.repository.publisher_repository import PublisherRepository
from sdk.celery.app import celery_app
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams

logger = logging.getLogger(__name__)

MODULE_ID = "moduleId"
MODULE_CONFIG_ID = "moduleConfigId"
DEPLOYMENT_ID = "deploymentId"
DEVICE_NAME = "deviceName"
PRIMITIVES = "primitives"


@celery_app.task
def publish_data_task(
    primitive_data: list[dict],
    module_id: str,
    device_name: str,
    module_config_id: str,
    deployment_id: str,
):
    """celery task to publish the event if there exists a registered publisher for it"""
    primitive_data = [PrimitiveData(**kwargs) for kwargs in primitive_data]
    event = recreate_event(
        primitive_data, module_id, device_name, module_config_id, deployment_id
    )

    skip = 0
    total = 0
    batch_size = 10

    publisher_repo: PublisherRepository = inject.instance(PublisherRepository)
    # retrieve publisher list
    while skip == 0 or skip < total:
        publishers, total = publisher_repo.retrieve_publishers(
            skip=skip, limit=batch_size
        )

        for publisher in publishers:
            # ignore the publisher if it is disabled
            if not publisher.enabled:
                continue

            # check list of registered publisher and see if it matches
            # if it does send the result to the endpoint specified
            matched = match_publisher_and_event(publisher, event)

            if not matched:
                continue

            logger.debug(f"Publisher Matched for deployment: {event['deploymentId']}")

            adapter = None

            if publisher.target.publisherType == Publisher.Target.Type.WEBHOOK:
                adapter = WebhookAdapter(publisher=publisher)
            elif publisher.target.publisherType == Publisher.Target.Type.KAFKA:
                adapter = KafkaAdapter(publisher=publisher)
            elif publisher.target.publisherType == Publisher.Target.Type.GCPFHIR:
                adapter = GCPFHIRAdapter(publisher=publisher)

            if publisher.filter.eventType == Publisher.Filter.EventType.PING:
                adapter.send_ping()
                continue

            event_copy = copy.deepcopy(event)
            adapter.transform_publisher_data(event_copy)

            if adapter.prepare_publisher_data(event_copy):
                adapter.send_publisher_data()

        if not total:
            break

        skip += batch_size


@autoparams("org_repo")
def match_publisher_and_event(
    publisher: Publisher, event: dict, org_repo: OrganizationRepository
) -> bool:
    """check event with publisher parameters see if it is a match"""

    matched = False

    if publisher.filter.listenerType == Publisher.Filter.ListenerType.ORGANIZATION_IDS:
        matched = match_publisher_and_event_org(
            publisher.filter.organizationIds, event, org_repo
        )
    elif publisher.filter.listenerType == Publisher.Filter.ListenerType.DEPLOYMENT_IDS:
        matched = match_publisher_and_event_deployment(
            publisher.filter.deploymentIds, event
        )
    elif publisher.filter.listenerType == Publisher.Filter.ListenerType.GLOBAL:
        matched = True

    if not matched:
        return False

    matched = False

    # also match if we have the module result we want to publish
    if publisher.filter.moduleNames:
        if event[MODULE_ID] in publisher.filter.moduleNames:
            matched = True
    if not publisher.filter.moduleNames:
        matched = True

    if publisher.filter.excludedModuleNames:
        if event[MODULE_ID] in publisher.filter.excludedModuleNames:
            matched = False
    return matched


@autoparams("repo")
def recreate_event(
    primitive_data: list[PrimitiveData],
    module_id: str,
    device_name: str,
    module_config_id: str,
    deployment_id: str,
    repo: ModuleResultRepository,
) -> dict:
    event = {}

    # create the event here
    primitives = [
        get_primitive_dict(repo.retrieve_primitive(p.user_id, p.name, p.id))
        for p in primitive_data
    ]

    event[DEVICE_NAME] = device_name
    event[MODULE_ID] = module_id
    event[PRIMITIVES] = primitives
    event[MODULE_CONFIG_ID] = module_config_id
    event[DEPLOYMENT_ID] = deployment_id

    return event


def match_publisher_and_event_org(
    organization_ids: list[str], event: dict, org_repo: OrganizationRepository
) -> bool:
    deployment_ids_o = []
    matched = False

    for organizationId in organization_ids:
        organization = org_repo.retrieve_organization(organization_id=organizationId)
        deployment_ids_o.extend(organization.deploymentIds)
    for deployment_id in deployment_ids_o:
        if event[DEPLOYMENT_ID] == str(deployment_id):
            matched = True

    return matched


def match_publisher_and_event_deployment(
    deployment_ids: list[str], event: dict
) -> bool:
    matched = False

    for deployment_id in deployment_ids:
        if event[DEPLOYMENT_ID] == str(deployment_id):
            matched = True

    return matched
