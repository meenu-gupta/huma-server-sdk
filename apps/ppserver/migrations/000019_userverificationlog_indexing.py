from sdk.common.mongodb_migrations.base import BaseMigration

_collections_to_be_created = ["verificationlog"]
_user_id_index = {"keys": "userId"}
_applicant_id_index = {"keys": "applicantId"}
_collection_index_map = {"verificationlog": [_user_id_index, _applicant_id_index]}


class Migration(BaseMigration):
    def upgrade(self):
        self.upgrade_base(_collection_index_map, _collections_to_be_created)

    def downgrade(self):
        pass
