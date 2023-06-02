import unittest
from unittest.mock import MagicMock

import bson

from extensions.authorization.models.user import User
from extensions.authorization.repository.mongo_user_repository import (
    MongoUserRepository,
)


class MongoUserRepositoryTestCase(unittest.TestCase):
    def test_success_retrieve_user_dict_by_id(self):
        mock_db = MagicMock()
        repo = MongoUserRepository(database=mock_db)
        uid = "609e78c47afa95a67586e527"
        repo.retrieve_user_dict_by_id(uid)
        mock_db[repo.USER_COLLECTION].find_one.assert_called_once_with(
            {User.ID_: bson.ObjectId(uid)}
        )

    def test_failure_retrieve_user_dict_by_id__not_object_id(self):
        mock_db = MagicMock()
        repo = MongoUserRepository(database=mock_db)
        uid = "111"
        with self.assertRaises(bson.errors.InvalidId):
            repo.retrieve_user_dict_by_id(uid)


if __name__ == "__main__":
    unittest.main()
