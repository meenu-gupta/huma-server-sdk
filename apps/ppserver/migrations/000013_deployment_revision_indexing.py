import pymongo
from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["deploymentrevision"]

_name_index = {"keys": [("deploymentId", pymongo.ASCENDING), ("version", 1)]}
_collection_index_map = {"deploymentrevision": [_name_index]}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
