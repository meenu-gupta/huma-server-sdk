from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["adminip"]
_ip_unique_index = {"keys": "ip", "unique": True, "sparse": True}
_collection_index_map = {"adminip": [_ip_unique_index]}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
