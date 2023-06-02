from extensions.export_deployment.utils import set_proper_export_type
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.modules.modules_manager import ModulesManager
from sdk.common.mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    """
    This migration is used to update existing export processes with proper type.
    """

    def upgrade(self):
        set_proper_export_type(self.db)

    def downgrade(self):
        pass
