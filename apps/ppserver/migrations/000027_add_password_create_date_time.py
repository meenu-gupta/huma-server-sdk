from sdk.auth.model.auth_user import AuthUser
from sdk.common.mongodb_migrations.base import BaseMigration

auth_user_collection = "authuser"


class Migration(BaseMigration):
    def upgrade(self):
        users = self.db[auth_user_collection].find()
        if not users:
            return

        for user in users:
            password_update_date_time = user.get(AuthUser.PASSWORD_UPDATE_DATE_TIME)
            if not password_update_date_time:
                continue
            self.db[auth_user_collection].update_one(
                {"_id": user[AuthUser.ID_]},
                {
                    "$set": {
                        AuthUser.PASSWORD_CREATE_DATE_TIME: password_update_date_time
                    }
                },
            )

    def downgrade(self):
        pass
