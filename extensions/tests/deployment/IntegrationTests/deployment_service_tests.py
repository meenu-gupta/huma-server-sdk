from pathlib import Path

from bson import ObjectId

from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.deployment import (
    ModuleConfig,
    Deployment,
    OnboardingModuleConfig,
)
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.tests.shared.test_helpers import get_module_config
from extensions.tests.test_case import ExtensionTestCase

DEPLOYMENT_ID = "5d386cc6ff885918d96eda1e"


class DeploymentServiceTests(ExtensionTestCase):
    components = [DeploymentComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployment_service_dump.json")]

    def setUp(self):
        super(DeploymentServiceTests, self).setUp()
        self.service = DeploymentService()

    def test_create_module_config(self):
        module_config = ModuleConfig.from_dict(get_module_config())
        config_id = self.service.create_module_config(DEPLOYMENT_ID, module_config)
        deployment_count = self.mongo_database.deployment.count_documents(
            {f"{Deployment.MODULE_CONFIGS}.{ModuleConfig.ID}": ObjectId(config_id)}
        )
        self.assertEqual(1, deployment_count)

    def test_create_onboarding_module_config(self):
        config_dict = {
            OnboardingModuleConfig.ONBOARDING_ID: "Consent",
            OnboardingModuleConfig.ORDER: 1,
        }
        config = OnboardingModuleConfig.from_dict(config_dict)
        config_id = self.service.create_onboarding_module_config(DEPLOYMENT_ID, config)
        deployment_count = self.mongo_database.deployment.count_documents(
            {f"{Deployment.ONBOARDING_CONFIGS}.{ModuleConfig.ID}": ObjectId(config_id)}
        )
        self.assertEqual(1, deployment_count)
