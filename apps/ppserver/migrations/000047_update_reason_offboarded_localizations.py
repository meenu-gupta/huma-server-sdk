from extensions.deployment.models.deployment import Reason
from sdk.common.mongodb_migrations.base import BaseMigration
from tools.mongodb_script.update_offboarding_reasons_localization import (
    update_offboarding_localizations,
)


class Migration(BaseMigration):
    def upgrade(self):
        default_reasons = Reason._default_reasons()
        update_offboarding_localizations(self.db, default_reasons)

    def downgrade(self):
        pass
