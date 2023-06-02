from bson import ObjectId

from extensions.authorization.models.user import User
from extensions.key_action.use_case.key_action_requests import (
    CreateKeyActionLogRequestObject,
)
from sdk.calendar.models.mongo_calendar_event import MongoCalendarEventLog
from sdk.common.mongodb_migrations.base import BaseMigration

log_collection_name = "calendarlog"
user_collection_name = "user"


class Migration(BaseMigration):
    def upgrade(self):
        calendar_logs = list(self.db[log_collection_name].find({}))
        if not calendar_logs:
            return

        user_ids = list(
            {log[CreateKeyActionLogRequestObject.USER_ID] for log in calendar_logs}
        )
        timezones_dict = self.get_user_timezones(user_ids)
        for log_dict in calendar_logs:
            mongo_log = MongoCalendarEventLog(**log_dict)
            dict_ = mongo_log.to_dict()

            # remove non-allowed fields
            id_ = dict_.pop("id")
            del dict_[CreateKeyActionLogRequestObject.UPDATE_DATE_TIME]
            del dict_[CreateKeyActionLogRequestObject.CREATE_DATE_TIME]

            log = CreateKeyActionLogRequestObject.from_dict(dict_)
            tz = timezones_dict.get(log.userId)
            if not tz or tz == "UTC":
                print(f"Skipping update for user {log.userId} as timezone is {tz}")
                continue

            # convert to local timezone
            log.as_timezone(tz)

            self.save_log(id_, log)

    def get_user_timezones(self, user_ids: list[ObjectId]) -> dict:
        fields = {User.ID_: 1, User.TIMEZONE: 1}

        result = self.db[user_collection_name].find(
            {User.ID_: {"$in": user_ids}}, fields
        )
        return {str(item[User.ID_]): item[User.TIMEZONE] for item in result}

    def save_log(self, id_, log: CreateKeyActionLogRequestObject):
        update_dict = {
            CreateKeyActionLogRequestObject.START_DATE_TIME: log.startDateTime,
            CreateKeyActionLogRequestObject.END_DATE_TIME: log.endDateTime,
        }
        self.db[log_collection_name].update_one(
            {"_id": ObjectId(id_)}, {"$set": update_dict}
        )

    def downgrade(self):
        pass
