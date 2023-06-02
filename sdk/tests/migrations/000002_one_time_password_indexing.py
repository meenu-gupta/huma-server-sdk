from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["onetimepassword"]
_id_index = {"keys": "identifier", "unique": True}
_date_index = {"keys": "createdAt", "unique": True, "expireAfterSeconds": 600}
_collection_index_map = {"onetimepassword": [_id_index, _date_index]}


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
