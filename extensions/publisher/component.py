import logging
from typing import Optional, Union, List

from flask import Blueprint

from extensions.module_result.event_bus.post_create_module_results_batch_event import (
    PostCreateModuleResultBatchEvent,
)
from extensions.publisher.callbacks.publisher_callback import publisher_callback
from extensions.publisher.config.config import PublisherConfig
from extensions.publisher.repository.mongo_publisher_repository import (
    MongoPublisherRepository,
)
from extensions.publisher.repository.publisher_repository import PublisherRepository
from extensions.publisher.router.publisher_router import publisher_route
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils.inject import Binder, autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class PublisherComponent(PhoenixBaseComponent):
    config_class = PublisherConfig
    tag_name = "publisher"

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        binder.bind_to_provider(PublisherRepository, lambda: MongoPublisherRepository())
        logger.debug("PublisherRepository bind to MongoPublisherRepository")

    @property
    def blueprint(self) -> Optional[Union[Blueprint, List[Blueprint]]]:
        return publisher_route

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        event_bus.subscribe(PostCreateModuleResultBatchEvent, publisher_callback)
        super().post_setup()
