from datetime import datetime

from pymongo.database import Database

from extensions.exceptions import RevereTestDoesNotExist
from extensions.revere.models.revere import RevereTest, RevereTestResult
from extensions.revere.repository.revere_repository import RevereTestRepository
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import id_as_obj_id, remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig


class MongoRevereTestRepository(RevereTestRepository):
    REVERE_TEST_COLLECTION = "reveretest"
    REVERE_WORD_LIST_COLLECTION = "revere_word_list"
    HOMOPHONES_COLLECTION = "revere_homophones"

    @autoparams()
    def __init__(self, database: Database):
        self._config = inject.instance(PhoenixServerConfig)
        self._db = database

    @id_as_obj_id
    def create_test(self, user_id: str, deployment_id: str, module_name: str) -> str:

        data = {
            RevereTest.USER_ID: user_id,
            RevereTest.START_DATE_TIME: datetime.utcnow(),
            RevereTest.RESULTS: [],
            RevereTest.STATUS: RevereTest.Status.STARTED.value,
            RevereTest.DEPLOYMENT_ID: deployment_id,
            RevereTest.MODULE_ID: module_name,
        }
        res = self._db[self.REVERE_TEST_COLLECTION].insert_one(data)
        return str(res.inserted_id)

    @id_as_obj_id
    def retrieve_test(self, user_id: str, test_id: str):
        res = self._db[self.REVERE_TEST_COLLECTION].find_one(
            {RevereTest.ID_: test_id, RevereTest.USER_ID: user_id}
        )
        if res is None:
            raise RevereTestDoesNotExist

        res[RevereTest.ID] = str(res.pop(RevereTest.ID_))

        return RevereTest.from_dict(res)

    @id_as_obj_id
    def retrieve_user_tests(self, user_id: str, status: str) -> [RevereTest]:
        query = {RevereTest.USER_ID: user_id, RevereTest.STATUS: status}
        res = self._db[self.REVERE_TEST_COLLECTION].find(remove_none_values(query))
        tests = []
        for test_dict in res:
            test = RevereTest.from_dict(
                test_dict,
                ignored_fields=[RevereTest.START_DATE_TIME, RevereTest.END_DATE_TIME],
            )
            test.id = str(test_dict[RevereTest.ID_])
            tests.append(test)

        return tests

    @id_as_obj_id
    def finish_test(self, user_id: str, test_id: str) -> None:
        self._db[self.REVERE_TEST_COLLECTION].update_one(
            {RevereTest.ID_: test_id, RevereTest.USER_ID: user_id},
            {
                "$set": {
                    RevereTest.END_DATE_TIME: datetime.utcnow(),
                    RevereTest.STATUS: RevereTest.Status.FINISHED.value,
                }
            },
        )

    @id_as_obj_id
    def save_word_list_result(
        self, test_id: str, user_id: str, result: RevereTestResult
    ) -> None:
        result.createDateTime = datetime.utcnow()

        updated_result = self._db[self.REVERE_TEST_COLLECTION].update_one(
            {
                RevereTest.ID_: test_id,
                RevereTest.USER_ID: user_id,
            },
            {"$push": {RevereTest.RESULTS: result.to_dict(include_none=False)}},
        )
        if updated_result.matched_count == 0:
            raise InvalidRequestException
