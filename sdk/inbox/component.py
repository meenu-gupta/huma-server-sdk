from typing import Optional, Union

from flask import Blueprint

import logging
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.inbox.events.auth_events import InboxAuthEvent
from sdk.inbox.repo.mongo_inbox_repository import (
    MongoInboxRepository,
)
from sdk.inbox.repo.inbox_repository import InboxRepository
from sdk.inbox.router.inbox_router import api
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig, InboxConfig

logger = logging.getLogger(__name__)


class InboxComponent(PhoenixBaseComponent):
    config_class = InboxConfig
    component_type = "sdk"
    tag_name = "Inbox"
    router = api

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        binder.bind_to_provider(InboxRepository, lambda: MongoInboxRepository())

        logger.debug(f"InboxRepository bind to MongoInboxRepository")

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return self.router

    def setup_auth(self):
        super(InboxComponent, self).setup_auth()
        blueprint = self.blueprint

        @blueprint.before_request
        def _setup_authz():
            server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
            config = getattr(server_config.server, self.tag_name)
            if config.enableAuth and config.enableAuthz:
                event_bus = inject.instance(EventBusAdapter)
                event_bus.emit(InboxAuthEvent(), raise_error=True)
