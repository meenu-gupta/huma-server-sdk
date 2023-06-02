from typing import Optional, Union

from flask import Blueprint

from extensions.authorization.di.components import PostCreateUserEvent
from extensions.authorization.events import PostUserProfileUpdateEvent
from extensions.deployment.events import (
    PostCreateKeyActionConfigEvent,
    PostUpdateKeyActionConfigEvent,
    PostDeleteKeyActionConfigEvent,
)
from extensions.key_action.callbacks.key_action_callback import (
    create_log_callback,
    on_user_delete_callback,
    create_key_actions_events,
    create_key_action_config_callback,
    create_surgery_key_action_on_user_change,
    update_key_actions_on_care_plan_group_change,
    update_key_actions_events,
    delete_key_action_config_callback,
)
from extensions.key_action.config.config import KeyActionConfig
from extensions.key_action.models.key_action_log import KeyAction
from extensions.key_action.router.key_action_router import key_action_route
from extensions.module_result.event_bus.post_create_primitive import (
    PostCreatePrimitiveEvent,
)
from sdk.auth.events.delete_user_event import DeleteUserEvent
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils.inject import autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent


class KeyActionComponent(PhoenixBaseComponent):
    config_class = KeyActionConfig
    tag_name = "keyAction"

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return key_action_route

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        CalendarEvent.register(KeyAction.__name__, KeyAction)
        event_subscriptions = [
            (PostCreatePrimitiveEvent, create_log_callback),
            (PostUserProfileUpdateEvent, create_surgery_key_action_on_user_change),
            (PostCreateUserEvent, create_key_actions_events),
            (PostCreateKeyActionConfigEvent, create_key_action_config_callback),
            (PostUpdateKeyActionConfigEvent, update_key_actions_events),
            (PostDeleteKeyActionConfigEvent, delete_key_action_config_callback),
            (PostUserProfileUpdateEvent, update_key_actions_on_care_plan_group_change),
            (DeleteUserEvent, on_user_delete_callback),
        ]
        for event, callback in event_subscriptions:
            event_bus.subscribe(event, callback)

        super().post_setup()
