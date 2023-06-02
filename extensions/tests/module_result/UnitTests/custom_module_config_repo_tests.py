import unittest
from unittest.mock import MagicMock, patch

from extensions.module_result.models.module_config import (
    CustomModuleConfig,
    CustomModuleConfigLogType,
)
from extensions.module_result.repository.custom_module_config_repository import (
    CustomModuleConfigRepository,
)
from extensions.module_result.repository.mongo_custom_module_config_repository import (
    MongoCustomModuleConfigRepository,
)
from extensions.tests.module_result.UnitTests.test_helpers import (
    sample_custom_module_config,
    SAMPLE_OBJECT_ID,
)
from sdk.common.utils import inject

REPO_PATH = "extensions.module_result.repository.mongo_custom_module_config_repository"


class ModuleResultsTestCase(unittest.TestCase):
    def setUp(self):
        def bind(binder):
            binder.bind_to_provider(CustomModuleConfigRepository, MagicMock())

        inject.clear_and_configure(bind)

    @patch(f"{REPO_PATH}.MongoCustomModuleConfigLog")
    @patch(f"{REPO_PATH}.MongoCustomModuleConfig")
    def test_create_custom_module_config(self, model, log_model):
        repo = MongoCustomModuleConfigRepository()
        custom_config = CustomModuleConfig.from_dict(sample_custom_module_config())
        repo.create_or_update_custom_module_config(
            module_config_id=SAMPLE_OBJECT_ID,
            module_config=custom_config,
            user_id=SAMPLE_OBJECT_ID,
            clinician_id=SAMPLE_OBJECT_ID,
        )
        model.objects.assert_called_with(userId=SAMPLE_OBJECT_ID, id=SAMPLE_OBJECT_ID)
        model.objects().first().update.assert_called_once()
        log_model.save = MagicMock()

    @patch(f"{REPO_PATH}.MongoCustomModuleConfig")
    def test_retrieve_custom_module_configs(self, model):
        repo = MongoCustomModuleConfigRepository()
        repo.retrieve_custom_module_configs(user_id=SAMPLE_OBJECT_ID)
        model.objects.assert_called_with(userId=SAMPLE_OBJECT_ID)

    @patch(f"{REPO_PATH}.MongoCustomModuleConfigLog")
    def test_retrieve_custom_module_config_logs(self, model):
        repo = MongoCustomModuleConfigRepository()
        repo.retrieve_custom_module_config_logs(
            user_id=SAMPLE_OBJECT_ID,
            module_config_id=SAMPLE_OBJECT_ID,
            log_type=CustomModuleConfigLogType.RAG,
        )
        model.objects.assert_called_with(
            userId=SAMPLE_OBJECT_ID, moduleConfigId=SAMPLE_OBJECT_ID
        )


if __name__ == "__main__":
    unittest.main()
