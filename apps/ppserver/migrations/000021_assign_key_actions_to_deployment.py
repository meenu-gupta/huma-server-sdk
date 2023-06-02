from bson import ObjectId

from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.key_action.models.key_action_log import KeyAction
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.mongodb_migrations.base import BaseMigration
from sdk.common.utils.validators import remove_none_values


class Migration(BaseMigration):
    user_deployments = {}
    key_action_config_deployments = {}

    def upgrade(self):
        query = {CalendarEvent.MODEL: KeyAction.__name__}
        key_actions = self.db["calendar"].find(query)
        for key_action in key_actions:
            extra_fields = key_action.get(CalendarEvent.EXTRA_FIELDS, {})
            key_action_config_id = extra_fields.get(KeyAction.KEY_ACTION_CONFIG_ID)
            user_id = str(key_action.get(CalendarEvent.USER_ID))
            deployment_id = self._get_deployment_id(key_action_config_id, user_id)
            if not deployment_id:
                continue
            update_query = {CalendarEvent.ID_: key_action[CalendarEvent.ID_]}
            key_action[KeyAction.EXTRA_FIELDS][KeyAction.DEPLOYMENT_ID] = deployment_id
            update_data = {"$set": key_action}
            self.db["calendar"].update_one(
                update_query, remove_none_values(update_data)
            )

    def downgrade(self):
        pass

    def _get_deployment_id(self, key_action_config_id: str, user_id: str):
        if not key_action_config_id:
            # getting first user's deployment
            user_deployment_id = self.user_deployments.get(user_id)
            if not user_deployment_id:
                user_deployment_id = self._get_deployment_from_user(user_id)
                self.user_deployments[user_id] = user_deployment_id
            return user_deployment_id
        # getting deployment based on key action config
        deployment_id = self.key_action_config_deployments.get(key_action_config_id)
        if not deployment_id:
            deployment_id = self._get_deployment_id_from_config(key_action_config_id)
            self.key_action_config_deployments[key_action_config_id] = deployment_id
        return deployment_id

    def _get_deployment_from_user(self, user_id):
        query = {User.ID_: ObjectId(user_id)}
        user_data = self.db[User.__name__.lower()].find_one(query)
        if not user_data:
            return
        user = User.from_dict(user_data, use_validator_field=False)
        return user.get_first_deployment_id()

    def _get_deployment_id_from_config(self, key_action_config_id):
        # query by KeyAction config id
        deployment_query = {
            Deployment.KEY_ACTIONS: {
                "$elemMatch": {KeyActionConfig.ID: ObjectId(key_action_config_id)}
            }
        }
        deployment = self.db[Deployment.__name__.lower()].find_one(deployment_query)
        if not deployment:
            return
        return str(deployment[Deployment.ID_])
