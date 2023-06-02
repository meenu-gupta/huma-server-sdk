from sdk.common.mongodb_migrations.base import BaseMigration

export_profiles_collection = "exportprofile"


class Migration(BaseMigration):
    def upgrade(self):
        collection = self.db.get_collection(export_profiles_collection)
        if collection is not None:
            # this will drop indexes for export profile collection
            # proper indexes will be recreated by mongoengine during any call to collection
            collection.drop_indexes()

    def downgrade(self):
        pass
