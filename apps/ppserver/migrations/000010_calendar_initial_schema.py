from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["calendar"]
_userId_index = {"keys": "userId"}
_enabled_index = {"keys": "enabled"}
_collection_index_map = {"calendar": [_userId_index, _enabled_index]}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
