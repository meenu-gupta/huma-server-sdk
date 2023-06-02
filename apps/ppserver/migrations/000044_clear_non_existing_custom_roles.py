from sdk.common.mongodb_migrations.base import BaseMigration
from tools.mongodb_script.remove_not_existing_roles import clear_roles


class Migration(BaseMigration):
    def upgrade(self):
        clear_roles(self.db)

    def downgrade(self):
        pass
