from extensions.module_result.calculate_unseen_and_recent_flags import UserFlagsStats
from sdk.common.mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    """
    This migration calculates RAG scores for all existing users
    """

    def upgrade(self):
        UserFlagsStats(self.db).calculate()

    def downgrade(self):
        pass
