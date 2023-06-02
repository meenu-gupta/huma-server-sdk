from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["closestevent"]
_user_id_index = {"keys": "userId"}
_collection_index_map = {"closestevent": [_user_id_index]}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
