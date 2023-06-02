from sdk.common.mongodb_migrations.base import BaseMigration
from extensions.deployment.models.deployment import Messaging

from tools.mongodb_script.add_message_to_deployment_without_message import (
    set_predefined_message_for_deployment_without_message,
    set_default_custom_flag_for_messages,
)

default_message = Messaging._default_message


class Migration(BaseMigration):
    def upgrade(self):
        set_predefined_message_for_deployment_without_message(self.db, default_message)
        set_default_custom_flag_for_messages(self.db)

    def downgrade(self):
        pass
