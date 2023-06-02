from extensions.organization.migration_utils import (
    set_dashboard_to_all_existing_organizations,
)
from sdk.common.mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    def upgrade(self):
        set_dashboard_to_all_existing_organizations(self.db)

    def downgrade(self):
        pass
