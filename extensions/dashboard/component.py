import logging
from typing import Optional, Union

from flask import Blueprint

from extensions.dashboard.router.dashboard_router import dashboard_route
from extensions.dashboard.config.config import DashboardConfig
from extensions.dashboard.di.components import bind_dashboard_repository
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils.inject import Binder, autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class DashboardComponent(PhoenixBaseComponent):
    config_class = DashboardConfig
    tag_name = "dashboard"
    _ignored_error_codes = ()

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return dashboard_route

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        super().post_setup()

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_dashboard_repository(binder)
