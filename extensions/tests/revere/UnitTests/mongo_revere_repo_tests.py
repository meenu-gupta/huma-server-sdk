import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId
from freezegun import freeze_time
from freezegun.api import FakeDatetime

from extensions.revere.models.revere import RevereTest, RevereTestResult
from extensions.revere.repository.mongo_revere_repository import (
    MongoRevereTestRepository,
)

MONGO_REPO_PATH = "extensions.revere.repository.mongo_revere_repository"
SAMPLE_ID = "600a8476a961574fb38157d5"
REVERE_COLLECTION = MongoRevereTestRepository.REVERE_TEST_COLLECTION


@patch(f"{MONGO_REPO_PATH}.inject", MagicMock())
class MongoRevereRepositoryTestCase(unittest.TestCase):
    @freeze_time("2012-01-01")
    def test_success_create_test(self):
        db = MagicMock()
        repo = MongoRevereTestRepository(database=db)
        user_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        module_name = "name"
        repo.create_test(
            user_id=user_id, deployment_id=deployment_id, module_name=module_name
        )
        db[REVERE_COLLECTION].insert_one.assert_called_with(
            {
                RevereTest.USER_ID: ObjectId(user_id),
                RevereTest.START_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                RevereTest.RESULTS: [],
                RevereTest.STATUS: RevereTest.Status.STARTED.value,
                RevereTest.DEPLOYMENT_ID: ObjectId(deployment_id),
                RevereTest.MODULE_ID: module_name,
            }
        )

    @patch(
        f"{MONGO_REPO_PATH}.RevereTest",
    )
    def test_success_retrieve_test(self, revere_test):
        db = MagicMock()
        repo = MongoRevereTestRepository(database=db)
        user_id = SAMPLE_ID
        test_id = SAMPLE_ID
        repo.retrieve_test(user_id=user_id, test_id=test_id)
        db[REVERE_COLLECTION].find_one.assert_called_with(
            {revere_test.ID_: ObjectId(test_id), revere_test.USER_ID: ObjectId(user_id)}
        )

    def test_success_retrieve_user_tests(self):
        user_id = SAMPLE_ID
        status = "status"
        db = MagicMock()
        repo = MongoRevereTestRepository(database=db)
        repo.retrieve_user_tests(user_id=user_id, status=status)
        db[REVERE_COLLECTION].find.assert_called_with(
            {RevereTest.USER_ID: ObjectId(user_id), RevereTest.STATUS: status}
        )

    @freeze_time("2012-01-01")
    def test_success_finish_test(self):
        user_id = SAMPLE_ID
        test_id = SAMPLE_ID
        db = MagicMock()
        repo = MongoRevereTestRepository(database=db)
        repo.finish_test(user_id=user_id, test_id=test_id)
        db[REVERE_COLLECTION].update_one.assert_called_with(
            {RevereTest.ID_: ObjectId(test_id), RevereTest.USER_ID: ObjectId(user_id)},
            {
                "$set": {
                    RevereTest.END_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                    RevereTest.STATUS: RevereTest.Status.FINISHED.value,
                }
            },
        )

    def test_success_save_word_list_result(self):
        test_id = SAMPLE_ID
        user_id = SAMPLE_ID
        word_list_id = SAMPLE_ID
        result_word_list = ["aaa", "bbb"]
        db = MagicMock()
        repo = MongoRevereTestRepository(database=db)
        result = RevereTestResult(
            wordsResult=result_word_list,
            id=word_list_id,
            createDateTime=datetime.utcnow(),
        )
        repo.save_word_list_result(test_id=test_id, user_id=user_id, result=result)
        db[REVERE_COLLECTION].update_one.assert_called_with(
            {RevereTest.ID_: ObjectId(test_id), RevereTest.USER_ID: ObjectId(user_id)},
            {"$push": {RevereTest.RESULTS: result.to_dict(include_none=False)}},
        )


if __name__ == "__main__":
    unittest.main()
