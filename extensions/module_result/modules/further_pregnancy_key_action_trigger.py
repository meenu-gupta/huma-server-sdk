from datetime import datetime
from typing import Union

import pytz

from extensions.authorization.models.user import User
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.key_action.models.key_action_log import KeyAction
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    AZFurtherPregnancyKeyActionTrigger,
    Primitive,
    CurrentGroupCategory,
    GroupCategory,
)
from extensions.module_result.modules.key_action_trigger import (
    KeyActionTriggerModule,
)
from extensions.module_result.modules.module import AzModuleMixin
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.exceptions.exceptions import InvalidModuleConfigBody
from sdk.common.utils.validators import utc_str_date_to_datetime


class AZFurtherPregnancyKeyActionTriggerModule(AzModuleMixin, KeyActionTriggerModule):
    KEY_ACTIONS_TO_REMOVE = "keyActionsToRemove"
    moduleId = "AZFurtherPregnancyKeyActionTrigger"
    primitives = [AZFurtherPregnancyKeyActionTrigger]

    @staticmethod
    def _delete_events(user: User, modules: list[str]):
        service = CalendarService()
        timezone = pytz.timezone(user.timezone)
        events = service.retrieve_all_calendar_events(
            timezone=timezone,
            **{
                CalendarEvent.MODEL: KeyAction.__name__,
                f"{CalendarEvent.EXTRA_FIELDS}.{CalendarEvent.MODULE_ID}": {
                    "$in": modules
                },
                CalendarEvent.USER_ID: user.id,
            },
        )
        events_to_remove = {event.id for event in events if event.enabled}

        service.batch_delete_calendar_events_by_ids(list(events_to_remove))

    def _remove_previous_key_actions(
        self,
        user: User,
        config_body: dict,
        previous_group: GroupCategory,
        current_group: CurrentGroupCategory,
    ):
        key_actions_to_remove: dict = config_body[self.KEY_ACTIONS_TO_REMOVE]
        key_action_groups: dict = key_actions_to_remove.get(
            GroupCategory(previous_group).name
        )
        modules = key_action_groups.get(CurrentGroupCategory(current_group).name)

        if modules:
            self._delete_events(user, modules)

    def trigger_key_actions(
        self,
        user: User,
        key_actions: list[KeyActionConfig],
        primitive: Primitive,
        config_body: dict,
        deployment_id: str,
        start_date: Union[str, datetime] = None,
        group_category: GroupCategory = None,
    ):

        key_action_groups: dict = config_body[self.KEY_ACTIONS]
        primitive_dict = primitive.to_dict(include_none=False)
        current_group = primitive_dict[
            AZFurtherPregnancyKeyActionTrigger.CURRENT_GROUP_CATEGORY
        ]
        modules = key_action_groups.get(CurrentGroupCategory(current_group).name)

        if current_group == CurrentGroupCategory.PREGNANT:
            self._remove_previous_key_actions(
                user=user,
                config_body=config_body,
                previous_group=group_category,
                current_group=current_group,
            )

        for module_id in modules:
            key_action_configs = [
                key_action
                for key_action in key_actions
                if key_action.moduleId == module_id
                and key_action.trigger == KeyActionConfig.Trigger.MANUAL
            ]

            self._create_key_actions(
                utc_str_date_to_datetime(start_date),
                user,
                key_action_configs,
                deployment_id,
            )

    def validate_config_body(self, module_config: ModuleConfig):
        super(AZFurtherPregnancyKeyActionTriggerModule, self).validate_config_body(
            module_config
        )
        config_body = module_config.configBody

        key_actions: dict = config_body.get("keyActions", None)
        if key_actions is None:
            msg = "'keyActions' field is required"
            raise InvalidModuleConfigBody(msg)

        missing_keys = []
        for category in CurrentGroupCategory:
            key = CurrentGroupCategory(category).name
            if key_actions.get(key) is None:
                missing_keys.append(key)

        if missing_keys:
            msg = f"[{', '.join(missing_keys)}] missing from 'keyActions' Object"
            raise InvalidModuleConfigBody(msg)
