from sdk.common.mongodb_migrations.base import BaseMigration
from tools.mongodb_script.move_labels_from_feature_to_deployment_level import (
    move_labels_from_feature_to_deployment_level,
)


class Migration(BaseMigration):
    def upgrade(self):
        move_labels_from_feature_to_deployment_level(self.db)

    def downgrade(self):
        pass
