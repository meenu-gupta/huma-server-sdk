import unittest
from unittest.mock import patch, MagicMock

from extensions.deployment.models.status import EnableStatus
from extensions.deployment.router.deployment_requests import (
    CreateMultipleModuleConfigsRequestObject,
    CreateModuleConfigRequestObject,
)
from extensions.deployment.use_case.add_multiple_module_configs_use_case import (
    CreateMultipleModuleConfigsUseCase,
)

USE_CASE_PATH = "extensions.deployment.use_case.add_multiple_module_configs_use_case"
SAMPLE_VALID_OBJ = "61cd5d79035d689ea79dd02b"


class CreateMultipleModuleConfigsUseCaseTestCase(unittest.TestCase):
    @patch(
        "extensions.module_result.models.module_config.ModuleConfig.validate",
        MagicMock(),
    )
    @patch(f"{USE_CASE_PATH}.DeploymentService")
    def test_success_create_multiple_module_configs_process_request(self, service):
        module_config = {"moduleId": "Journal", "status": EnableStatus.ENABLED.value}
        req_obj = CreateMultipleModuleConfigsRequestObject.from_dict(
            {
                CreateMultipleModuleConfigsRequestObject.DEPLOYMENT_ID: SAMPLE_VALID_OBJ,
                CreateMultipleModuleConfigsRequestObject.MODULE_CONFIGS: [
                    module_config,
                ],
            }
        )
        CreateMultipleModuleConfigsUseCase().execute(req_obj)
        service().create_module_config.assert_called_with(
            SAMPLE_VALID_OBJ, CreateModuleConfigRequestObject.from_dict(module_config)
        )


if __name__ == "__main__":
    unittest.main()
