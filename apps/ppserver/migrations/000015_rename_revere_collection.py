from bson import ObjectId

from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.repository.mongo_user_repository import (
    MongoUserRepository,
)
from extensions.module_result.modules.revere_test import RevereTestModule
from extensions.revere.models.revere import RevereTest, RevereTestResult
from sdk.common.mongodb_migrations.base import BaseMigration
from sdk.common.utils.validators import remove_none_values

old_revere_collection_name = "revere_test"
actual_revere_collection_name = "reveretest"


class Migration(BaseMigration):
    def upgrade(self):
        collections = self.db.list_collection_names()
        if old_revere_collection_name in collections:
            self.db[old_revere_collection_name].rename(actual_revere_collection_name)
        revere_tests = self.db[actual_revere_collection_name].find()
        for test in revere_tests:
            query = {RevereTest.ID_: test[RevereTest.ID_]}
            module_id = RevereTestModule.moduleId
            new_values = {RevereTest.MODULE_ID: module_id}

            if results := test.get(RevereTest.RESULTS):
                deployment_id = results[0][RevereTestResult.DEPLOYMENT_ID]
                new_values[RevereTest.DEPLOYMENT_ID] = deployment_id
            else:
                user_id = test[RevereTest.USER_ID]
                user = self.db[MongoUserRepository.USER_COLLECTION].find_one(
                    {User.ID_: user_id}
                )
                user_roles = user.get(User.ROLES)
                if not user_roles:
                    continue
                deployment_id = user[User.ROLES][0][RoleAssignment.RESOURCE].split("/")[
                    -1
                ]
                new_values[RevereTest.DEPLOYMENT_ID] = ObjectId(deployment_id)

            unset_data = None
            if RevereTest.END_DATE_TIME in test and not test[RevereTest.END_DATE_TIME]:
                unset_data = {RevereTest.END_DATE_TIME: 1}

            self.db[actual_revere_collection_name].update_one(
                query, remove_none_values({"$set": new_values, "$unset": unset_data})
            )

    def downgrade(self):
        pass
