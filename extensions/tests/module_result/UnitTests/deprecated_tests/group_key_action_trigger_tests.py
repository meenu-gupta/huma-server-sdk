import datetime
import unittest
from unittest.mock import MagicMock, patch

from extensions.module_result.models.primitives import (
    AZGroupKeyActionTrigger,
    GroupCategory,
)
from extensions.module_result.modules import AZGroupKeyActionTriggerModule
from .group_information_primitive_tests import (
    AZGroupKeyActionTriggerTestCase,
)
from extensions.tests.module_result.UnitTests.primitives_tests import COMMON_FIELDS

SAMPLE_ID = "617659773959892aab507949"
PATH = "extensions.module_result.modules.group_key_action_trigger"


class AZGroupKeyActionTriggerModuleTestCase(unittest.TestCase):
    @patch(f"{PATH}.AZGroupKeyActionTriggerModule._create_key_actions")
    def test_trigger_key_actions(self, create_key_action):
        user = MagicMock()
        key_actions = [MagicMock()]
        AZGroupKeyActionTriggerTestCase._assign_primitive_values()
        primitive = AZGroupKeyActionTrigger.create_from_dict(
            COMMON_FIELDS, name="AZGroupKeyActionTrigger"
        )
        config_body = {
            AZGroupKeyActionTriggerModule.KEY_ACTIONS: {
                GroupCategory.MALE_OR_FEMALE_OVER_50.name: [MagicMock()]
            }
        }
        deployment_id = "deployment_id"
        module = AZGroupKeyActionTriggerModule()
        module.trigger_key_actions(
            user, key_actions, primitive, config_body, deployment_id
        )
        create_key_action.assert_called_with(
            datetime.datetime(2019, 6, 30, 0, 0), user, [], deployment_id
        )


if __name__ == "__main__":
    unittest.main()
