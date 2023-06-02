from typing import Optional, Union

from flask import Blueprint

from extensions.config.config import MedicationTrackerConfig
from extensions.medication.callbacks.callbacks import on_user_delete_callback
from extensions.medication.di.components import bind_medication_repository
from extensions.medication.router.medication_router import api
from sdk.auth.events.delete_user_event import DeleteUserEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils.inject import Binder, autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig


class MedicationComponent(PhoenixBaseComponent):
    config_class = MedicationTrackerConfig
    tag_name = "medication"

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_medication_repository(binder, config)

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return api

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        event_bus.subscribe(DeleteUserEvent, on_user_delete_callback)
        super().post_setup()
