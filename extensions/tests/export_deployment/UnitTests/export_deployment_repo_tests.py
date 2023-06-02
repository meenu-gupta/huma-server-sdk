import unittest
from unittest.mock import MagicMock, patch

from extensions.authorization.models.user import User
from extensions.export_deployment.models.export_deployment_models import ExportProcess
from extensions.export_deployment.repository.mongo_export_deployment_repository import (
    MongoExportDeploymentRepository,
)


MONGO_REPO_PATH = (
    "extensions.export_deployment.repository.mongo_export_deployment_repository"
)


class ExportDeploymentRepoTestCase(unittest.TestCase):
    def test_retrieve_user_use_validator_field_is_called(self):
        deployment_id = "601a7761b2a1b1d3bfc24b0f"
        user = {User.ID_: "601a77fa06c1cba10050b16b", User.HEIGHT: 10}
        mockdb = MagicMock()
        mockdb[MongoExportDeploymentRepository.USER_COLLECTION].find = MagicMock(
            return_value=[user]
        )
        repo = MongoExportDeploymentRepository(mockdb)
        try:
            res = repo.retrieve_users(deployment_id)
        except Exception:
            self.fail()
        else:
            self.assertEqual(res[0].height, 10.0)

    @patch(f"{MONGO_REPO_PATH}.MongoExportProcess")
    def test_retrieve_unseen_export_process_count(self, model):
        user_id = "12345678"
        expected_call = {
            ExportProcess.REQUESTER_ID: user_id,
            ExportProcess.SEEN: False,
        }
        repo = MongoExportDeploymentRepository(MagicMock())
        repo.retrieve_unseen_export_process_count(user_id)
        model.objects.assert_called_with(**expected_call)


if __name__ == "__main__":
    unittest.main()
