from bson import ObjectId

from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.repository.mongo_user_repository import (
    MongoUserRepository,
)
from extensions.module_result.modules import MedicationsModule
from extensions.medication.models.medication import Medication
from sdk.common.mongodb_migrations.base import BaseMigration
from sdk.common.utils.validators import remove_none_values

medication_collection = Medication.__name__.lower()


class Migration(BaseMigration):
    def upgrade(self):
        medications = self.db[medication_collection].find()
        for medication in medications:
            user_id = medication[Medication.USER_ID]
            user = self.db[MongoUserRepository.USER_COLLECTION].find_one(
                {User.ID_: user_id}
            )
            if not user:
                continue
            user_roles = user.get(User.ROLES)
            if not user_roles:
                continue
            deployment_id = user[User.ROLES][0][RoleAssignment.RESOURCE].split("/")[-1]
            if not ObjectId.is_valid(deployment_id):
                continue

            query = {Medication.ID_: medication[Medication.ID_]}

            # this is needed to have correct history
            medication[Medication.DEPLOYMENT_ID] = ObjectId(deployment_id)
            medication[Medication.MODULE_ID] = MedicationsModule.moduleId
            set_values = {
                Medication.MODULE_ID: medication[Medication.MODULE_ID],
                Medication.DEPLOYMENT_ID: medication[Medication.DEPLOYMENT_ID],
            }
            push_values = None
            history = medication.get(Medication.CHANGE_HISTORY)
            if not history:
                set_values[Medication.CHANGE_HISTORY] = [
                    {**medication, "changeType": "MEDICATION_CREATE"}
                ]
            else:
                # deleting history to avoid writing it into history
                del medication[Medication.CHANGE_HISTORY]
                history_data = {**medication, "changeType": "MEDICATION_UPDATE"}
                push_values = {Medication.CHANGE_HISTORY: history_data}
            update_data = {"$set": set_values, "$push": push_values}
            self.db[medication_collection].update_one(
                query, remove_none_values(update_data)
            )

    def downgrade(self):
        pass
