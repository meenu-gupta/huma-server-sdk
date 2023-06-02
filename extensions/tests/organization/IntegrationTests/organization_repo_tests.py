from pathlib import Path

from extensions.dashboard.models.dashboard import DashboardId
from extensions.organization.component import OrganizationComponent
from extensions.organization.migration_utils import (
    set_dashboard_to_all_existing_organizations,
)
from extensions.organization.models.organization import Organization
from extensions.organization.repository.mongo_organization_repository import (
    MongoOrganizationRepository,
)
from extensions.tests.test_case import ExtensionTestCase

COLLECTION_NAME = MongoOrganizationRepository.ORGANIZATION_COLLECTION


class OrganizationRepoTestCase(ExtensionTestCase):
    components = [
        OrganizationComponent(),
    ]

    fixtures = [Path(__file__).parent.joinpath("fixtures/organization_dump.json")]

    def test_set_dashboard_to_all_existing_organizations(self):
        res_before_update = self.mongo_database[COLLECTION_NAME].find()
        for item in res_before_update:
            self.assertNotIn(Organization.DASHBOARD_ID, item)

        set_dashboard_to_all_existing_organizations(self.mongo_database)
        res_after_update = self.mongo_database[COLLECTION_NAME].find()
        for item in res_after_update:
            self.assertEqual(
                DashboardId.ORGANIZATION_OVERVIEW.value, item[Organization.DASHBOARD_ID]
            )
