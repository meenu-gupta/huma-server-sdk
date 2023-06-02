from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_dropped = ["closestevent"]
_collections_to_be_created = ["nextdayevent"]
_user_id_index = {"keys": "userId"}
_parent_id_index = {"keys": "parentId"}
_collection_index_map = {"nextdayevent": [_user_id_index, _parent_id_index]}


class Migration(BaseMigration):
    def upgrade(self):
        # drop closestevent collection
        for collection in _collections_to_be_dropped:
            self.db.get_collection(collection).drop()

        # create nextdayevent collection with indexes
        self.upgrade_base(_collection_index_map, _collections_to_be_created)
        # prepare_events_for_next_day.delay()

    def downgrade(self):
        pass
