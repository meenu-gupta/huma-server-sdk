from extensions.authorization.models.invitation import Invitation
from extensions.authorization.models.user import RoleAssignment
from sdk.common.mongodb_migrations.base import BaseMigration

invitations_collection = "invitation"


class Migration(BaseMigration):
    """This migration uses role assignment in invitation instead of flat resources and role ids"""

    def upgrade(self):
        invitations = self.db[invitations_collection].find()
        if not invitations:
            return
        for invitation in invitations:
            roles = []
            deployment_ids = invitation.pop("deploymentIds", None)
            organization_id = invitation.pop("organizationId", None)
            role_id = invitation.pop("roleId", None)

            if not role_id:
                continue

            if deployment_ids:
                for deployment_id in deployment_ids:
                    roles.append(
                        {
                            RoleAssignment.ROLE_ID: role_id,
                            RoleAssignment.RESOURCE: f"deployment/{deployment_id}",
                        }
                    )

            if organization_id:
                roles.append(
                    {
                        RoleAssignment.ROLE_ID: role_id,
                        RoleAssignment.RESOURCE: f"organization/{organization_id}",
                    }
                )

            invitation[Invitation.ROLES] = roles
            self.db[invitations_collection].update_one(
                {Invitation.ID_: invitation[Invitation.ID_]},
                {
                    "$set": invitation,
                    "$unset": {"deploymentIds": 1, "organizationId": 1, "roleId": 1},
                },
            )

    def downgrade(self):
        pass
