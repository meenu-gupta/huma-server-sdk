from extensions.export_deployment.models.export_deployment_models import ExportProcess
from sdk.common.mongodb_migrations.base import BaseMigration

collection = ExportProcess.__name__.lower()


class Migration(BaseMigration):
    def upgrade(self):
        update = {
            "$set": {ExportProcess.EXPORT_TYPE: ExportProcess.ExportType.DEFAULT.value}
        }
        self.db[collection].update_many({}, update)

    def downgrade(self):
        pass
