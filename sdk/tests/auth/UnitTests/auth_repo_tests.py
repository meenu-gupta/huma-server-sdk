import unittest
from unittest.mock import MagicMock, patch

from bson import ObjectId

from sdk.auth.model.auth_user import AuthUser
from sdk.auth.model.session import DeviceSession
from sdk.auth.repository.mongo_auth_repository import MongoAuthRepository

USER_ID = "600a8476a961574fb38157d5"

MOCK_DB = MagicMock()


class MockMongoClient:
    instance = MagicMock()
    get_database = MagicMock(return_value=MOCK_DB)
    session = MagicMock()
    start_session = MagicMock(return_value=session)


class MockInject:
    instance = MagicMock()


class AuthRepoTestCase(unittest.TestCase):
    @patch("sdk.auth.repository.mongo_auth_repository.inject", MockInject)
    def test_success_delete_user(self):
        mongo_client = MockMongoClient()
        repo = MongoAuthRepository(client=mongo_client)
        repo.delete_user(user_id=USER_ID)
        user_id = ObjectId(USER_ID)
        MOCK_DB[repo.USER_COLLECTION].delete_one.assert_called_with(
            {AuthUser.ID_: user_id}, session=mongo_client.session
        )
        MOCK_DB[repo.SESSION_COLLECTION].delete_many.assert_called_with(
            {DeviceSession.USER_ID: user_id}, session=mongo_client.session
        )


if __name__ == "__main__":
    unittest.main()
