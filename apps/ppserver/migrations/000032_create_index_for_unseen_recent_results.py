from sdk.common.mongodb_migrations.base import BaseMigration

unseen_primitive_collection = "unseenrecentresult"


class Migration(BaseMigration):
    def upgrade(self):
        collection = self.db.get_collection(unseen_primitive_collection)
        if collection is None:
            self.db.create_collection(unseen_primitive_collection)
            collection = self.db.get_collection(unseen_primitive_collection)
        collection.create_index("userId")

    def downgrade(self):
        pass
