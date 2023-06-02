import logging

from extensions.module_result.event_bus.post_create_module_results_batch_event import (
    PostCreateModuleResultBatchEvent,
)
from extensions.publisher.models.primitive_data import PrimitiveData
from extensions.publisher.tasks import publish_data_task

logger = logging.getLogger(__name__)


def publisher_callback(event: PostCreateModuleResultBatchEvent, run_async=True):
    logger.debug(f"PostCreateModuleResultBatchEvent for {event.module_id}")

    primitive_data = [
        {
            PrimitiveData.ID: primitive.id,
            PrimitiveData.NAME: key,
            PrimitiveData.USER_ID: primitive.userId,
        }
        for key, primitive in event.primitives.items()
    ]

    args = [
        primitive_data,
        event.module_id,
        event.device_name,
        event.module_config_id,
        event.deployment_id,
    ]
    if run_async:
        publish_data_task.delay(*args)
    else:
        publish_data_task(*args)
