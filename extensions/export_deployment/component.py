import logging
from typing import Optional, Union

from flask import Blueprint

from extensions.authorization.events.get_badges_event import GetUserBadgesEvent
from extensions.export_deployment.exceptions import ExportErrorCodes
from extensions.export_deployment.callbacks import get_async_export_badges
from extensions.export_deployment.config.config import ExportDeploymentConfig
from extensions.export_deployment.di.components import (
    bind_source_db_client_and_database,
    bind_export_repositories,
)
from extensions.export_deployment.router.export_deployment_routers import (
    api as export_deployment_route,
)
from extensions.export_deployment.router.report_routers import api as report_route
from extensions.export_deployment.router.user_export_routers import (
    api as user_export_route,
)
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils.inject import Binder, autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class ExportDeploymentComponent(PhoenixBaseComponent):
    config_class = ExportDeploymentConfig
    tag_name = "exportDeployment"
    tasks = ["extensions.export_deployment"]
    _ignored_error_codes = (
        ExportErrorCodes.DUPLICATE_PROFILE_NAME,
        ExportErrorCodes.PROCESS_IN_PROGRESS,
    )

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_source_db_client_and_database(binder, config)
        bind_export_repositories(binder)

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        blueprints = [export_deployment_route, user_export_route]
        if self.config.summaryReportEnabled:
            blueprints.append(report_route)
        return blueprints

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        event_bus.subscribe(GetUserBadgesEvent, get_async_export_badges)
        return super().post_setup()
