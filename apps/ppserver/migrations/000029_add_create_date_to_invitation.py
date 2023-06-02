from datetime import datetime

import jwt
import pytz

from extensions.authorization.models.invitation import Invitation
from sdk.common.mongodb_migrations.base import BaseMigration

invitations_collection = "invitation"


class Migration(BaseMigration):
    """This migration is used to add expiresAt for existing invitations"""

    def upgrade(self):
        invitations = self.db[invitations_collection].find()
        if not invitations:
            return
        for invitation in invitations:
            created = invitation.get(Invitation.CREATE_DATE_TIME)
            code = invitation.get(Invitation.CODE)
            if created or not code:
                continue
            try:
                data = jwt.decode(code, verify=False)
            except jwt.DecodeError:
                continue
            created_timestamp = data.get("iat")
            if not created_timestamp:
                continue
            created_at = datetime.fromtimestamp(created_timestamp, pytz.UTC)
            self.db[invitations_collection].update_one(
                {Invitation.ID_: invitation[Invitation.ID_]},
                {"$set": {Invitation.CREATE_DATE_TIME: created_at}},
            )

    def downgrade(self):
        pass
