from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["device"]
_user_id_index = {"keys": "userId"}
_device_id_unique_index = {"keys": "deviceId", "unique": True, "sparse": True}
_collection_index_map = {"device": [_user_id_index, _device_id_unique_index]}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
