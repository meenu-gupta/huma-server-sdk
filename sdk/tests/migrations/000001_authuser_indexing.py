from sdk.common.mongodb_migrations.base import BaseMigration

"""
reindexing
"""
_collections_to_be_created = ["authuser"]
_email_index = {"keys": "email", "unique": True, "sparse": True}
_phone_index = {"keys": "phoneNumber", "unique": True, "sparse": True}
_collection_index_map = {"authuser": [_email_index, _phone_index]}


class Migration(BaseMigration):
    def upgrade(self):
        existing_collections = self.db.list_collection_names()
        # 1. removing all indexes
        for k in _collection_index_map.keys():
            collection = self.db.get_collection(k)
            if collection is not None:
                collection.drop_indexes()
        # 2. recreate indexes
        for c in _collections_to_be_created:
            if c not in existing_collections:
                self.db.create_collection(c)
            if c in _collection_index_map:
                for i in _collection_index_map.get(c):
                    self.db.get_collection(c).create_index(**i)

    def downgrade(self):
        pass
