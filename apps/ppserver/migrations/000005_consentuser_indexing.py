from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["consentlog"]
_user_id_index = {"keys": "userId"}
_consent_id_index = {"keys": "consentId"}
_revision_index = {"keys": "revision"}
_collection_index_map = {
    "consentlog": [_user_id_index, _consent_id_index, _revision_index]
}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
