from extensions.authorization.models.user import User
from extensions.export_deployment.models.export_deployment_models import (
    ExportProfile,
    ExportParameters,
)

from sdk.common.mongodb_migrations.base import BaseMigration

export_profiles_collection = "exportprofile"
old_sample = (
    User.TAGS,
    User.TAGS_AUTHOR_ID,
    User.ROLES,
    "latestModuleResults",
    User.RECENT_MODULE_RESULTS,
)


class Migration(BaseMigration):
    def upgrade(self):
        export_profiles = self.db[export_profiles_collection].find()
        if not export_profiles:
            return

        for profile in export_profiles:
            profile_content = profile.get(ExportProfile.CONTENT)
            exclude_fields = profile_content.get(ExportParameters.EXCLUDE_FIELDS, [])
            if exclude_fields:
                for i, field in enumerate(exclude_fields):
                    if field in old_sample:
                        exclude_fields[i] = f"user.{field}"
            self.db[export_profiles_collection].update_one(
                {"_id": profile[ExportProfile.ID_]}, {"$set": profile}
            )

    def downgrade(self):
        pass
