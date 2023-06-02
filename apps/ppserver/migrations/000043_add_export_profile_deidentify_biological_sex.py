from datetime import datetime

from extensions.authorization.models.user import User
from extensions.export_deployment.models.export_deployment_models import (
    ExportProfile,
    ExportParameters,
)
from sdk.common.mongodb_migrations.base import BaseMigration

export_profiles_collection = "exportprofile"


class Migration(BaseMigration):
    def upgrade(self):
        export_profiles = self.db[export_profiles_collection].find()
        if not export_profiles:
            return

        for profile in export_profiles:
            profile_content = profile.get(ExportProfile.CONTENT)
            deidentify_fields = profile_content.get(
                ExportParameters.DE_IDENTIFY_REMOVE_FIELDS, []
            )
            deidentify_fields.append(User.BIOLOGICAL_SEX)
            deidentify_fields.append(User.DATE_OF_BIRTH)
            deidentify_fields[:] = list(set(deidentify_fields))
            profile[ExportProfile.UPDATE_DATE_TIME] = datetime.utcnow()
            self.db[export_profiles_collection].update_one(
                {ExportProfile.ID_: profile[ExportProfile.ID_]}, {"$set": profile}
            )

    def downgrade(self):
        pass
