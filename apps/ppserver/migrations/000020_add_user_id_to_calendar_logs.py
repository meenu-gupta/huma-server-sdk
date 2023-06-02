from sdk.calendar.models.calendar_event import CalendarEventLog, CalendarEvent
from sdk.common.mongodb_migrations.base import BaseMigration

calendar_collection = "calendar"
calendar_log_collection = "calendarlog"


class Migration(BaseMigration):
    def upgrade(self):
        parent_ids = self.retrieve_parent_ids()
        user_ids = self.retrieve_user_ids_dict(parent_ids)
        for parent_id in parent_ids:
            self.db[calendar_log_collection].update_many(
                {CalendarEventLog.PARENT_ID: parent_id},
                {"$set": {CalendarEventLog.USER_ID: user_ids.get(str(parent_id))}},
            )

    def retrieve_parent_ids(self):
        collection = self.db.get_collection(calendar_log_collection)
        results = collection.find({}, {CalendarEventLog.PARENT_ID: 1})
        return [result[CalendarEventLog.PARENT_ID] for result in results]

    def retrieve_user_ids_dict(self, parent_ids: list) -> dict:
        collection = self.db.get_collection(calendar_collection)
        projection = {CalendarEvent.USER_ID: 1}
        results = collection.find({"_id": {"$in": parent_ids}}, projection)
        return {str(result["_id"]): result[CalendarEvent.USER_ID] for result in results}

    def downgrade(self):
        pass
