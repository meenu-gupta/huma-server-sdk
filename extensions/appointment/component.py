import logging
from typing import Optional, Union

from flask import Blueprint

from extensions.appointment.callbacks import get_appointment_badge
from extensions.appointment.di.components import bind_appointment_repository
from extensions.appointment.exceptions import AppointmentErrorCodes
from extensions.appointment.models.appointment import Appointment
from extensions.appointment.models.appointment_event import AppointmentEvent
from extensions.appointment.router.appointment_router import appointment_route
from extensions.authorization.events.get_badges_event import GetUserBadgesEvent
from extensions.config.config import AppointmentConfig
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils.inject import Binder, autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class AppointmentComponent(PhoenixBaseComponent):
    config_class = AppointmentConfig
    tag_name = "appointment"
    _ignored_error_codes = (AppointmentErrorCodes.INVALID_DATE,)

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return appointment_route

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        CalendarEvent.register(Appointment.__name__, AppointmentEvent)
        super().post_setup()
        event_bus.subscribe(GetUserBadgesEvent, get_appointment_badge)

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_appointment_repository(binder)
