from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["onetimepassword"]
_id_index = {"keys": "identifier", "unique": True}
_date_index = {"keys": "createdAt", "unique": True, "expireAfterSeconds": 600}
_collection_index_map = {"onetimepassword": [_id_index, _date_index]}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
