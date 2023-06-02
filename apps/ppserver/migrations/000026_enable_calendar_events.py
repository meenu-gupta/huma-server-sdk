from sdk.common.mongodb_migrations.base import BaseMigration

calendar_collection = "calendar"


class Migration(BaseMigration):
    def upgrade(self):
        self.db[calendar_collection].update_many({}, {"$set": {"enabled": True}})

    def downgrade(self):
        pass
