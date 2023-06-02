from sdk.common.mongodb_migrations.base import BaseMigration
from tools.mongodb_script.migrate_country_to_location_in_deployment import (
    move_country_to_location,
)


class Migration(BaseMigration):
    def upgrade(self):
        move_country_to_location(self.db)

    def downgrade(self):
        pass
