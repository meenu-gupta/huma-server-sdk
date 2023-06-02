from unittest import TestCase
from unittest.mock import MagicMock

from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.module_result.models.module_config import ModuleConfig
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.utils import inject


def get_deployment():
    return Deployment(
        id="611e03b4f5150b8148acdadf",
        name="test",
        moduleConfigs=[
            ModuleConfig(id="611e033cf5150b8148acdad0"),
            ModuleConfig(id="611e0357f5150b8148acdad1"),
            ModuleConfig(id="611e035ff5150b8148acdad2"),
        ],
        keyActions=[
            KeyActionConfig(
                id="611e035ff5150b8148acdad3", moduleConfigId="611e033cf5150b8148acdad0"
            ),
            KeyActionConfig(
                id="611e035ff5150b8148acdad4", moduleConfigId="611e033cf5150b8148acdad0"
            ),
            KeyActionConfig(
                id="611e035ff5150b8148acdad5", moduleConfigId="611e035ff5150b8148acdad1"
            ),
            KeyActionConfig(id="611e035ff5150b8148acdad6", moduleConfigId=None),
        ],
    )


class MockRepo(MagicMock):
    delete_module_config = MagicMock()
    delete_key_action = MagicMock()
    retrieve_deployment = MagicMock()
    retrieve_deployment.return_value = get_deployment()
    _post_key_action_delete = MagicMock()
    store_deployment = MagicMock()


class DeleteModuleConfigTests(TestCase):
    def setUp(self):
        def bind(binder):
            binder.bind(FileStorageAdapter, MagicMock())

        inject.clear_and_configure(bind)

    # tuple of test cases -> (deployment_id, moduleConfigId, related key actions count)
    test_map = (
        ("test", "611e033cf5150b8148acdad0", 2),
        ("test", "611e035ff5150b8148acdad1", 1),
        ("test", "611e035ff5150b8148acdad2", 0),
    )

    @staticmethod
    def reset_mock():
        MockRepo.retrieve_deployment.reset_mock()
        MockRepo.retrieve_deployment.return_value = get_deployment()
        MockRepo.delete_key_action.reset_mock()

    def test_delete_module_config_with_two_key_actions(self):
        service = DeploymentService(
            MockRepo(), None, None, MagicMock(), MagicMock(), None
        )
        for test_case in self.test_map:
            self.reset_mock()
            service._post_key_action_delete = MagicMock()

            deployment_id, module_config_id, expected_count = test_case
            service.delete_module_config(deployment_id, module_config_id)
            MockRepo.retrieve_deployment.assert_called_once()
            self.assertEqual(expected_count, MockRepo.delete_key_action.call_count)
            self.assertEqual(expected_count, service._post_key_action_delete.call_count)
