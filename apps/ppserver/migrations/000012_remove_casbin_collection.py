from sdk.common.mongodb_migrations.base import BaseMigration

collection = "casbin_rule"


class Migration(BaseMigration):
    def upgrade(self):
        self.db[collection].drop()

    def downgrade(self):
        pass
