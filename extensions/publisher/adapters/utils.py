from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.publisher.models.publisher import Publisher
from sdk.common.utils.inject import autoparams
from extensions.export_deployment.helpers.convertion_helpers import (
    get_consents_meta_data_with_deployment,
    attach_users,
    deidentify_dict,
    exclude_fields,
    filter_not_included_fields,
)
from sdk.common.utils.validators import remove_none_values

MODULE_ID = "moduleId"
MODULE_CONFIG_ID = "moduleConfigId"
DEPLOYMENT_ID = "deploymentId"
DEVICE_NAME = "deviceName"
PRIMITIVES = "primitives"


@autoparams("deployment_repo")
def transform_publisher_data(
    publisher: Publisher, event: dict, deployment_repo: DeploymentRepository
):
    """filter and transform data here based on the input parameters
    (deIdentify, include-exclude, attach user meta, ...)"""

    primitives = event[PRIMITIVES]

    event_data = {event[MODULE_ID]: primitives}

    deployment = deployment_repo.retrieve_deployment(deployment_id=event[DEPLOYMENT_ID])
    users_data = {}

    if publisher.transform.includeUserMetaData:
        consents_meta, econsents_meta = get_consents_meta_data_with_deployment(
            deployment
        )

        attach_users(
            consents_meta,
            econsents_meta,
            publisher.transform.includeNullFields,
            users_data,
            event_data,
            deployment,
        )
    for primitive in primitives:
        filter_not_included_fields(publisher.transform.includeFields, primitive)

    exclude_fields(event_data, publisher.transform.excludeFields)

    for primitive in primitives:
        deidentify_dict(
            primitive,
            publisher.transform.excludeFields,
            publisher.transform.deIdentified,
            publisher.transform.deIdentifyRemoveFields,
            publisher.transform.deIdentifyHashFields,
        )

    if not publisher.transform.includeNullFields:
        event[PRIMITIVES] = remove_none_values(primitives)
