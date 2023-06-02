import unittest
from unittest.mock import patch, MagicMock

import pytz

from extensions.key_action.models.key_action_log import KeyAction
from extensions.module_result.event_bus.base_primitive_event import BasePrimitiveEvent
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    GroupCategory,
    CurrentGroupCategory,
    Primitive,
    AZFurtherPregnancyKeyActionTrigger,
)
from extensions.module_result.modules import AZFurtherPregnancyKeyActionTriggerModule
from extensions.module_result.modules.key_action_trigger import KeyActionTriggerModule
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_further_information,
)
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.exceptions.exceptions import InvalidModuleConfigBody

PATH = "extensions.module_result.modules.further_pregnancy_key_action_trigger"
SAMPLE_ID = "617659773959892aab507949"


class AZFurtherPregnancyKeyActionTriggerModuleTestCase(unittest.TestCase):
    @patch(f"{PATH}.CalendarService")
    def test_delete_events(self, service):
        user = MagicMock()
        user.timezone = "UTC"
        modules = ["first_module", "sec_module"]
        AZFurtherPregnancyKeyActionTriggerModule._delete_events(user, modules)
        service().retrieve_all_calendar_events.assert_called_with(
            timezone=pytz.UTC,
            model=KeyAction.__name__,
            **{
                f"{CalendarEvent.EXTRA_FIELDS}.{CalendarEvent.MODULE_ID}": {
                    "$in": modules
                }
            },
            userId=user.id,
        )
        service().batch_delete_calendar_events_by_ids.assert_called_with([])

    @patch(f"{PATH}.AZFurtherPregnancyKeyActionTriggerModule._delete_events")
    def test_remove_previous_key_actions(self, delete_events):
        user = MagicMock()
        modules = ["aa"]
        config_body = {
            AZFurtherPregnancyKeyActionTriggerModule.KEY_ACTIONS_TO_REMOVE: {
                GroupCategory.PREGNANT.name: {GroupCategory.PREGNANT.name: modules}
            }
        }
        previous_group = GroupCategory.PREGNANT
        current_group = CurrentGroupCategory.PREGNANT
        module = AZFurtherPregnancyKeyActionTriggerModule()
        module._remove_previous_key_actions(
            user, config_body, previous_group, current_group
        )
        delete_events.assert_called_with(user, modules)

    @patch(
        f"{PATH}.AZFurtherPregnancyKeyActionTriggerModule._remove_previous_key_actions"
    )
    def test_trigger_key_actions(self, remove_prev_key_actions):
        user = MagicMock()
        key_actions = [MagicMock()]
        primitive_data = {
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            **sample_further_information(),
        }
        primitive = AZFurtherPregnancyKeyActionTrigger.from_dict(primitive_data)
        config_body = {
            KeyActionTriggerModule.KEY_ACTIONS: {CurrentGroupCategory.PREGNANT.name: {}}
        }
        deployment_id = "deployment_id"
        module = AZFurtherPregnancyKeyActionTriggerModule()
        module.trigger_key_actions(
            user, key_actions, primitive, config_body, deployment_id
        )
        remove_prev_key_actions.assert_called_with(
            user=user,
            config_body={
                BasePrimitiveEvent.KEY_ACTIONS: {CurrentGroupCategory.PREGNANT.name: {}}
            },
            previous_group=None,
            current_group=0,
        )

    def test_validate_config_body(self):
        module = AZFurtherPregnancyKeyActionTriggerModule()
        config_body = {
            KeyActionTriggerModule.KEY_ACTIONS: {
                CurrentGroupCategory.PREGNANT.name: {},
                CurrentGroupCategory.NOT_PREGNANT.name: {},
            }
        }
        module_config = ModuleConfig(configBody=config_body)
        try:
            module.validate_config_body(module_config)
        except InvalidModuleConfigBody:
            self.fail()


if __name__ == "__main__":
    unittest.main()
