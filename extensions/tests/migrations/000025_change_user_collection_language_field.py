import pymongo

from sdk.common.mongodb_migrations.base import BaseMigration

_collection_name = "user"
_index_name = "givenName_text_familyName_text"
_name_index = {
    "keys": [("givenName", pymongo.TEXT), ("familyName", pymongo.TEXT)],
    "language_override": "noLangField",
}


class Migration(BaseMigration):
    def upgrade(self):
        if _collection_name not in self.db.list_collection_names():
            return

        indexes = [dict(index) for index in self.db["user"].list_indexes()]
        name_index = next(filter(lambda x: x["name"] == _index_name, indexes), None)
        if name_index:
            # if field is not language - all good, stop migration
            if name_index.get("language_override", None) != "language":
                return

            # otherwise drop index
            self.db["user"].drop_index(_index_name)

        # create a new proper index
        self.db["user"].create_index(**_name_index)

    def downgrade(self):
        pass
