from pathlib import Path

from extensions.deployment.component import DeploymentComponent
from extensions.export_deployment.component import ExportDeploymentComponent
from extensions.export_deployment.repository.mongo_export_deployment_repository import (
    MongoExportDeploymentRepository,
)
from extensions.tests.test_case import ExtensionTestCase


class ExportDeploymentsTestCase(ExtensionTestCase):
    components = [
        DeploymentComponent(),
        ExportDeploymentComponent(),
    ]
    migration_path: str = str(Path(__file__).parent.parent.parent) + "/migrations"
    VALID_USER_ID = "5e8f0c74b50aa9656c34789c"
    VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
    API_URL = f"/api/extensions/v1beta/export/deployment/{VALID_DEPLOYMENT_ID}"
    fixtures = [Path(__file__).parent.joinpath("fixtures/data.json")]

    def setUp(self):
        super().setUp()
        self._repo = MongoExportDeploymentRepository()

    def test_export_user_with_wrong_height(self):
        resp = self._repo.retrieve_users(deployment_id=self.VALID_DEPLOYMENT_ID)
        for user in resp:
            if user.id == self.VALID_USER_ID:
                self.assertEqual(user.height, 20.0)
