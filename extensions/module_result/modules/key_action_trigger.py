import logging
from datetime import datetime
from typing import Union

from extensions.authorization.models.user import User
from extensions.common.monitoring import report_exception
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.key_action.callbacks.key_action_generator import KeyActionGenerator
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.modules.module import Module
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.exceptions.exceptions import InvalidModuleConfigBody
from sdk.common.utils.validators import utc_str_val_to_field

logger = logging.getLogger(__name__)


class KeyActionTriggerModule(Module):
    KEY_ACTIONS = "keyActions"

    def _create_key_actions(
        self,
        start_date: Union[str, datetime],
        user: User,
        key_actions: list[KeyActionConfig],
        deployment_id,
    ):
        start = utc_str_val_to_field(start_date).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        service = CalendarService()
        for key_action in key_actions:
            try:
                generator = KeyActionGenerator(user, start, deployment_id)
                cal_event = generator.build_key_action_from_config(key_action)
                service.create_calendar_event(cal_event, user.timezone)
            except Exception as error:
                logger.error(
                    f"Key action was not created for user #{user.email}. Error: {error}"
                )
                report_exception(
                    error,
                    context_name="KeyActionTrigger",
                    context_content={
                        "userId": user.id,
                        "deploymentId": deployment_id,
                        "key_actions": [k.to_dict() for k in key_actions],
                    },
                )

    def validate_config_body(self, module_config: ModuleConfig):
        config_body = module_config.configBody

        if config_body is None:
            msg = f"configBody is required for {module_config.moduleId}"
            raise InvalidModuleConfigBody(msg)
