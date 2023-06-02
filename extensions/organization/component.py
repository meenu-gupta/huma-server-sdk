import logging
from typing import Optional, Union

from flask import Blueprint

from extensions.deployment.events import TargetConsentedUpdateEvent
from extensions.organization.callbacks.callbacks import process_target_consented_update
from extensions.organization.config.config import OrganizationConfig
from extensions.organization.di.components import bind_organization_repository
from extensions.organization.router.organization_router import organization_route
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils.inject import Binder, autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class OrganizationComponent(PhoenixBaseComponent):
    config_class = OrganizationConfig
    tag_name = "Organization"

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_organization_repository(binder, config)

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        subscriptions = list()
        subscriptions.append(
            (TargetConsentedUpdateEvent, process_target_consented_update)
        )

        for event, callback in subscriptions:
            event_bus.subscribe(event, callback)

        super().post_setup()

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return organization_route
