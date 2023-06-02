from datetime import datetime, timedelta

from extensions.authorization.models.invitation import Invitation
from sdk.common.mongodb_migrations.base import BaseMigration

invitations_collection = "invitation"


class Migration(BaseMigration):
    """This migration is used to add expiresAt for existing invitations"""

    def upgrade(self):
        expires_at = datetime.utcnow() + timedelta(
            days=1
        )  # current default expiration, as fallback
        self.db[invitations_collection].update_many(
            {Invitation.EXPIRES_AT: None},
            {"$set": {Invitation.EXPIRES_AT: expires_at}},
        )

    def downgrade(self):
        pass
