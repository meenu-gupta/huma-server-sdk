from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import BoardingStatus, User
from sdk.common.mongodb_migrations.base import BaseMigration
from sdk.common.utils.validators import remove_none_values

users_collection = "user"


class Migration(BaseMigration):
    """
    This migration sets a default value for boardingStatus field in user collection.
    This helps in enhancing filtering functionality.
    """

    def upgrade(self):
        query = {
            User.BOARDING_STATUS: {"$exists": False},
            "roles.roleId": {"$in": [RoleName.USER, RoleName.PROXY]},
        }

        default_status = BoardingStatus(status=BoardingStatus.Status.ACTIVE)
        default_status = remove_none_values(default_status.to_dict())
        update = {"$set": {User.BOARDING_STATUS: default_status}}

        self.db[users_collection].update_many(query, update)

    def downgrade(self):
        pass
