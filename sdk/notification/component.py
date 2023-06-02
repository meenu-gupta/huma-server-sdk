from typing import Optional, Union

from flask import Blueprint

import logging
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.notification.events.auth_events import NotificationAuthEvent
from sdk.notification.repository.mongo_notification_repository import (
    MongoNotificationRepository,
)
from sdk.notification.repository.notification_repository import NotificationRepository
from sdk.notification.router.notification_router import api
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig, NotificationConfig

logger = logging.getLogger(__name__)


class NotificationComponent(PhoenixBaseComponent):
    config_class = NotificationConfig
    component_type = "sdk"
    tag_name = "notification"
    router = api

    @property
    def api_specs(self):
        return {
            "endpoint": f"apispec_{self.name.lower()}",
            "route": f"/apispec_{self.name.lower()}.json",
            "rule_filter": None,
            "model_filter": lambda tag: True,  # all in
        }

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        binder.bind_to_provider(
            NotificationRepository, lambda: MongoNotificationRepository()
        )

        logger.debug(f"NotificationRepository bind to MongoNotificationRepository")

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return self.router

    def setup_auth(self):
        super(NotificationComponent, self).setup_auth()
        blueprint = self.blueprint

        @blueprint.before_request
        def _setup_authz():
            server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
            config = getattr(server_config.server, self.tag_name)
            if config.enableAuth and config.enableAuthz:
                event_bus = inject.instance(EventBusAdapter)
                event_bus.emit(NotificationAuthEvent(), raise_error=True)
