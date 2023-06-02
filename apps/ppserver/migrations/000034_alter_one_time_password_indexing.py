import pymongo

from sdk.common.mongodb_migrations.base import BaseMigration

one_time_password_collection = "onetimepassword"
identifier_index_name = "identifier_1"


class Migration(BaseMigration):
    def upgrade(self):
        collection = self.db.get_collection(one_time_password_collection)
        if collection is not None:
            collection.drop_index(identifier_index_name)
            collection.create_index(
                [("identifier", pymongo.ASCENDING), ("type", pymongo.ASCENDING)],
                unique=True,
            )

    def downgrade(self):
        pass
