import pymongo
from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["deployment"]
_name_index = {"keys": [("name", pymongo.TEXT)]}
_user_code_index = {"keys": "userActivationCode", "unique": True, "sparse": True}
_manager_code_index = {"keys": "managerActivationCode", "unique": True, "sparse": True}
_collection_index_map = {
    "deployment": [_name_index, _user_code_index, _manager_code_index]
}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
