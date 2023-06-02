from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["econsentlog"]
_user_id_index = {"keys": "userId"}
_econsent_id_index = {"keys": "econsentId"}
_revision_index = {"keys": "revision"}
_collection_index_map = {
    "econsentlog": [_user_id_index, _econsent_id_index, _revision_index]
}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
