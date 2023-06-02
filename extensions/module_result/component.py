from typing import Optional, Union

from flask import Blueprint

from extensions.config.config import ModuleResultConfig
from extensions.deployment.events import PostDeploymentUpdateEvent
from extensions.module_result.callbacks.callbacks import (
    on_user_delete_callback,
    check_retrieve_permissions,
    disable_schedule_events_callback,
)
from extensions.module_result.di.components import (
    bind_custom_module_config_repository,
    bind_module_result_repository,
    bind_pam_integration_client,
)
from extensions.module_result.event_bus.post_retrieve_primitive import (
    PostRetrievePrimitiveEvent,
)
from extensions.module_result.exceptions import ModuleResultErrorCodes
from extensions.module_result.models.scheduled_event import ScheduledEvent
from extensions.module_result.modules.module import Module
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from extensions.module_result.router.custom_module_config_router import (
    api as custom_module_config_router,
)
from extensions.module_result.router.module_result_router import (
    api as module_result_router,
)
from sdk.auth.events.delete_user_event import DeleteUserEvent
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder, autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig


class ModuleResultComponent(PhoenixBaseComponent):
    config_class = ModuleResultConfig
    tag_name = "moduleResult"
    _ignored_error_codes = (
        ModuleResultErrorCodes.MODULE_NOT_CONFIGURED,
        ModuleResultErrorCodes.NOT_ALL_QUESTIONS_ANSWERED,
    )
    _warn_error_codes = (ModuleResultErrorCodes.PRIMITIVE_NOT_REGISTERED,)

    def __init__(self, additional_modules: list[Module] = None):
        self.additional_modules = additional_modules

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_custom_module_config_repository(binder, config)
        bind_module_result_repository(binder, config)
        bind_pam_integration_client(binder, config)

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return [custom_module_config_router, module_result_router]

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        CalendarEvent.register(ScheduledEvent.__name__, ScheduledEvent)
        self._create_indexes()
        event_bus.subscribe(DeleteUserEvent, on_user_delete_callback)
        event_bus.subscribe(PostRetrievePrimitiveEvent, check_retrieve_permissions)
        event_bus.subscribe(PostDeploymentUpdateEvent, disable_schedule_events_callback)
        if self.additional_modules:
            manager = inject.instance(ModulesManager)
            manager.add_modules(self.additional_modules)

        super().post_setup()

    @autoparams()
    def _create_indexes(self, repo: ModuleResultRepository):
        repo.create_indexes()
