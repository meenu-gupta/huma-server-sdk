from sdk.common.mongodb_migrations.base import BaseMigration
from extensions.authorization.router.user_profile_request import SortParameters

user_collection = "user"


class Migration(BaseMigration):
    def upgrade(self):
        collection = self.db.get_collection(user_collection)
        if collection is None:
            self.db.create_collection(user_collection)
            collection = self.db.get_collection(user_collection)
        collection.create_index(SortParameters.Field.TASK_COMPLIANCE.value)

    def downgrade(self):
        pass
