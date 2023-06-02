from sdk.common.mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    """
    This migration adds a new field `lastSubmitDateTime` to all existing users.
    This is a dateTime field that shows when user last submitted module result.
    This will enhance sorting and filtering for user profile by increasing performance of queries.
    """

    def upgrade(self):
        pipeline = [
            {
                "$match": {
                    "recentModuleResults": {"$exists": True},
                    "lastSubmitDateTime": {"$exists": False},
                }
            },
            {"$addFields": {"lastResult": {"$objectToArray": "$recentModuleResults"}}},
            {"$unwind": {"path": "$lastResult"}},
            {"$addFields": {"lastResult": "$lastResult.v"}},
            {"$unwind": {"path": "$lastResult"}},
            {"$addFields": {"lastResult": {"$objectToArray": "$lastResult"}}},
            {"$addFields": {"lastResult": "$lastResult.v"}},
            {"$unwind": {"path": "$lastResult"}},
            {"$match": {"lastResult.isForManager": {"$ne": True}}},
            {"$sort": {"lastResult.createDateTime": -1}},
            {"$group": {"_id": "$_id", "lastSubmitResult": {"$first": "$lastResult"}}},
            {"$addFields": {"lastSubmitDateTime": "$lastSubmitResult.createDateTime"}},
            {"$unset": "lastSubmitResult"},
        ]
        users = self.db.user.aggregate(pipeline, allowDiskUse=True)
        for user in users:
            last_submitted = user.pop("lastSubmitDateTime", None)
            if last_submitted:
                self.db.user.update_one(
                    {"_id": user.pop("_id")},
                    {"$set": {"lastSubmitDateTime": last_submitted}},
                )

    def downgrade(self):
        pass
