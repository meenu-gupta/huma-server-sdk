from extensions.dashboard.models.dashboard import DashboardId
from extensions.organization.models.organization import Organization
from extensions.organization.repository.mongo_organization_repository import (
    MongoOrganizationRepository,
)


def set_dashboard_to_all_existing_organizations(db):
    collection = MongoOrganizationRepository.ORGANIZATION_COLLECTION
    db[collection].update_many(
        {},
        {"$set": {Organization.DASHBOARD_ID: DashboardId.ORGANIZATION_OVERVIEW.value}},
    )
