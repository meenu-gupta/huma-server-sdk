from sdk.common.mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    """
    This migration sets `finishedOnboarding=True` to users,
    that have submitted recentModuleResults.
    """

    def upgrade(self):
        self.db.user.update_many(
            {
                "finishedOnboarding": {"$ne": True},
                "recentModuleResults": {"$nin": [None, {}]},
            },
            {"$set": {"finishedOnboarding": True}},
        )

    def downgrade(self):
        pass
