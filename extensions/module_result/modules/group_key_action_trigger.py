from datetime import datetime
from typing import Union

from extensions.authorization.models.user import User
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    AZGroupKeyActionTrigger,
    Primitive,
    GroupCategory,
)
from extensions.module_result.modules.key_action_trigger import (
    KeyActionTriggerModule,
)
from extensions.module_result.modules.module import AzModuleMixin
from sdk.common.exceptions.exceptions import InvalidModuleConfigBody
from sdk.common.utils.validators import utc_str_date_to_datetime


class AZGroupKeyActionTriggerModule(AzModuleMixin, KeyActionTriggerModule):
    moduleId = "AZGroupKeyActionTrigger"
    primitives = [AZGroupKeyActionTrigger]

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
        group_category = primitive_dict[AZGroupKeyActionTrigger.GROUP_CATEGORY]
        start_date = primitive_dict[AZGroupKeyActionTrigger.FIRST_VACCINE_DATE]
        start_datetime = utc_str_date_to_datetime(start_date)
        modules = key_action_groups.get(GroupCategory(group_category).name)

        for module_id in modules:
            key_action_configs = [
                key_action
                for key_action in key_actions
                if key_action.moduleId == module_id
                and key_action.trigger == KeyActionConfig.Trigger.MANUAL
            ]

            self._create_key_actions(
                start_datetime, user, key_action_configs, deployment_id
            )

    def validate_config_body(self, module_config: ModuleConfig):
        super(AZGroupKeyActionTriggerModule, self).validate_config_body(module_config)
        config_body = module_config.configBody

        key_actions: dict = config_body.get("keyActions", None)
        if key_actions is None:
            msg = "'keyActions' field is required"
            raise InvalidModuleConfigBody(msg)

        missing_keys = []
        for category in GroupCategory:
            key = GroupCategory(category).name
            if key_actions.get(key) is None:
                missing_keys.append(key)

        if missing_keys:
            msg = f"[{', '.join(missing_keys)}] missing from 'keyActions' Object"
            raise InvalidModuleConfigBody(msg)
