from sdk.common.mongodb_migrations.base import BaseMigration

"""
reindexing
"""

_collections_to_be_created = ["authuser"]
_email_index = {"keys": "email", "unique": True, "sparse": True}
_phone_index = {"keys": "phoneNumber", "unique": True, "sparse": True}

_collection_index_map = {
    "authuser": [_email_index, _phone_index],
}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
