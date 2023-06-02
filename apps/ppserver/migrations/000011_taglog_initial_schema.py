from sdk.common.mongodb_migrations.base import BaseMigration

collection = "taglog"
_collections_to_be_created = [collection]
_userId_index = {"keys": "userId"}
_authorId_index = {"keys": "authorId"}
_collection_index_map = {collection: [_userId_index, _authorId_index]}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
