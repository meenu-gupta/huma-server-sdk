from typing import Optional, Union

from flask import Blueprint

from extensions.authorization.events import PostUserProfileUpdateEvent
from extensions.config.config import UserModuleReminderConfig
from extensions.reminder.callbacks.callbacks import (
    update_reminders_language_localization,
)
from extensions.reminder.models.reminder import UserModuleReminder
from extensions.reminder.router.user_module_reminder_router import api
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils.inject import autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent


class UserModuleReminderComponent(PhoenixBaseComponent):
    config_class = UserModuleReminderConfig
    tag_name = "userModuleReminder"

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return api

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        CalendarEvent.register(UserModuleReminder.__name__, UserModuleReminder)
        event_bus.subscribe(
            PostUserProfileUpdateEvent, update_reminders_language_localization
        )
        super().post_setup()
