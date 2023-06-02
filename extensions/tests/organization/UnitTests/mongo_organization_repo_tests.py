import unittest
from unittest.mock import MagicMock, patch

from bson import ObjectId
from freezegun import freeze_time
from freezegun.api import FakeDatetime
from pymongo.database import Database

from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.mongo_deployment_repository import (
    MongoDeploymentRepository,
)
from extensions.exceptions import (
    OrganizationDoesNotExist,
    DeploymentNotLinked,
)
from extensions.organization.models.organization import Organization
from extensions.organization.repository.mongo_organization_repository import (
    MongoOrganizationRepository,
)
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig

ORGANIZATION_REPO_PATH = (
    "extensions.organization.repository.mongo_organization_repository"
)
ORGANIZATION_COLLECTION = MongoOrganizationRepository.ORGANIZATION_COLLECTION
SAMPLE_ID = "600a8476a961574fb38157d5"


class MongoOrganizationRepositoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()

        def bind(binder):
            binder.bind(Database, self.db)
            binder.bind(PhoenixServerConfig, MagicMock())

        inject.clear_and_configure(bind)

    @freeze_time("2012-01-01")
    def test_success_create_organization(self):
        repo = MongoOrganizationRepository()
        organization = Organization.from_dict({Organization.NAME: "test_org_name"})
        repo.create_organization(organization=organization)
        self.db[ORGANIZATION_COLLECTION].insert_one.assert_called_with(
            {
                Organization.NAME: organization.name,
                Organization.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                Organization.CREATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
            }
        )

    def test_success_retrieve_organization(self):
        repo = MongoOrganizationRepository()
        organization_id = SAMPLE_ID
        repo.retrieve_organization(organization_id=organization_id)
        self.db[ORGANIZATION_COLLECTION].find_one.assert_called_with(
            {Organization.ID_: ObjectId(organization_id)}
        )

    def test_success_retrieve_organizations(self):
        repo = MongoOrganizationRepository()
        repo.retrieve_organizations()
        self.db[ORGANIZATION_COLLECTION].aggregate.assert_called_with(
            [
                {"$addFields": {"id": {"$toString": "$_id"}}},
                {"$match": {}},
                {
                    "$facet": {
                        "results": [{"$skip": 0}],
                        "totalCount": [{"$count": "count"}],
                    }
                },
            ]
        )

    def test_success_retrieve_organization_by_deployment_id(self):
        repo = MongoOrganizationRepository()
        deployment_id = SAMPLE_ID
        repo.retrieve_organization_by_deployment_id(deployment_id=deployment_id)
        self.db[ORGANIZATION_COLLECTION].find_one.assert_called_with(
            {Organization.DEPLOYMENT_IDS: deployment_id}
        )

    def test_success_retrieve_organization_ids(self):
        repo = MongoOrganizationRepository()
        deployment_ids = [SAMPLE_ID]
        repo.retrieve_organization_ids(deployment_ids=deployment_ids)
        self.db[ORGANIZATION_COLLECTION].find.assert_called_with(
            {
                Organization.DEPLOYMENT_IDS: {
                    "$elemMatch": {"$in": ["600a8476a961574fb38157d5"]}
                }
            },
            {Organization.ID_: 1},
        )

    @freeze_time("2012-01-01")
    def test_success_update_organization(self):
        repo = MongoOrganizationRepository()
        organization = Organization.from_dict({Organization.NAME: "test_org_name"})
        organization.id = ObjectId(SAMPLE_ID)
        repo.update_organization(organization=organization)
        self.db[ORGANIZATION_COLLECTION].find_one_and_update.assert_called_with(
            {Organization.ID_: ObjectId(SAMPLE_ID)},
            {
                "$set": {
                    Organization.NAME: "test_org_name",
                    Organization.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                }
            },
        )

    def test_success_delete_organization(self):
        repo = MongoOrganizationRepository()
        organization_id = SAMPLE_ID
        repo.delete_organization(organization_id=organization_id)
        self.db[ORGANIZATION_COLLECTION].find_one_and_delete.assert_called_with(
            {Organization.ID_: ObjectId(organization_id)}
        )

    @patch(
        f"{ORGANIZATION_REPO_PATH}.MongoOrganizationRepository._verify_unlink_deployment_result"
    )
    def test_success_unlink_deployment(self, verify_unlink_deployment_result):
        repo = MongoOrganizationRepository()
        organization_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        repo.unlink_deployment(
            organization_id=organization_id, deployment_id=deployment_id
        )
        filter_query = {Organization.ID_: ObjectId(organization_id)}
        update_query = {"$pull": {Organization.DEPLOYMENT_IDS: deployment_id}}

        self.db[ORGANIZATION_COLLECTION].update_one.assert_called_with(
            filter_query, update_query
        )
        verify_unlink_deployment_result.assert_called_with(
            self.db[ORGANIZATION_COLLECTION].update_one()
        )

    def test_success_link_deployment(self):
        repo = MongoOrganizationRepository()
        organization_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        repo.link_deployment(
            organization_id=organization_id, deployment_id=deployment_id
        )
        filter_query = {Organization.ID_: ObjectId(organization_id)}
        update_query = {"$push": {Organization.DEPLOYMENT_IDS: deployment_id}}

        self.db[ORGANIZATION_COLLECTION].update_one.assert_called_with(
            filter_query, update_query
        )

    @patch(f"{ORGANIZATION_REPO_PATH}.OrganizationWithDeploymentInfo")
    def test_success_retrieve_organization_with_deployment_data(self, obj):
        repo = MongoOrganizationRepository()
        organization_id = SAMPLE_ID
        sample_organization = MagicMock()
        sample_organization.deploymentIds = [SAMPLE_ID]
        obj.from_dict.return_value = sample_organization

        repo.retrieve_organization_with_deployment_data(organization_id=organization_id)
        self.db[ORGANIZATION_COLLECTION].find_one.assert_called_with(
            {Organization.ID_: ObjectId(organization_id)}
        )
        self.db[
            MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        ].find.assert_called_with(
            {Deployment.ID_: {"$in": [ObjectId(SAMPLE_ID)]}},
            projection={Deployment.ID_: 1, Deployment.NAME: 1},
        )

    def test_success_link_deployments(self):
        organization_id = SAMPLE_ID
        deployment_ids = [SAMPLE_ID, SAMPLE_ID]
        repo = MongoOrganizationRepository()
        repo.link_deployments(
            organization_id=organization_id, deployment_ids=deployment_ids
        )
        self.db[ORGANIZATION_COLLECTION].update_one.assert_called_with(
            {Organization.ID_: ObjectId(organization_id)},
            {"$addToSet": {Organization.DEPLOYMENT_IDS: {"$each": deployment_ids}}},
        )

    @patch(
        f"{ORGANIZATION_REPO_PATH}.MongoOrganizationRepository._verify_unlink_deployment_result"
    )
    def test_success_unlink_deployments(self, verify_unlink_deployment_result):
        organization_id = SAMPLE_ID
        deployment_ids = [SAMPLE_ID, SAMPLE_ID]
        repo = MongoOrganizationRepository()
        repo.unlink_deployments(
            organization_id=organization_id, deployment_ids=deployment_ids
        )
        self.db[ORGANIZATION_COLLECTION].update_one.assert_called_with(
            {Organization.ID_: ObjectId(organization_id)},
            {"$pull": {Organization.DEPLOYMENT_IDS: {"$in": deployment_ids}}},
        )
        verify_unlink_deployment_result.assert_called_with(
            self.db[ORGANIZATION_COLLECTION].update_one()
        )

    def test_retrieve_organization_by_name(self):
        repo = MongoOrganizationRepository()
        repo.retrieve_organization_by_name("some name")
        self.db[ORGANIZATION_COLLECTION].find_one.assert_called_with(
            {Organization.NAME: {"$regex": "^some\\ name$", "$options": "i"}}
        )

    def test_verify_unlink_deployment_result__no_matched_count(self):
        res = MagicMock(matched_count=0)
        with self.assertRaises(OrganizationDoesNotExist):
            MongoOrganizationRepository._verify_unlink_deployment_result(res)

    def test_verify_unlink_deployment_result__no_modified_count(self):
        res = MagicMock(modified_count=0)
        with self.assertRaises(DeploymentNotLinked):
            MongoOrganizationRepository._verify_unlink_deployment_result(res)

    def test_retrieve_organizations_by_ids(self):
        org_ids = [SAMPLE_ID, SAMPLE_ID, "*"]
        repo = MongoOrganizationRepository()
        repo.retrieve_organizations_by_ids(org_ids)
        self.db[ORGANIZATION_COLLECTION].find.assert_called_with(
            {Organization.ID_: {"$in": [ObjectId(id_) for id_ in org_ids[:2]]}}
        )


if __name__ == "__main__":
    unittest.main()
