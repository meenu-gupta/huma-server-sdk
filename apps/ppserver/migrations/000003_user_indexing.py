import pymongo
from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["user"]
_name_index = {
    "keys": [("givenName", pymongo.TEXT), ("familyName", pymongo.TEXT)],
    "language_override": "noLangField",
}
_email_index = {"keys": "email", "unique": True, "sparse": True}
_phone_index = {"keys": "phoneNumber", "unique": True, "sparse": True}
_collection_index_map = {"user": [_email_index, _phone_index, _name_index]}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
