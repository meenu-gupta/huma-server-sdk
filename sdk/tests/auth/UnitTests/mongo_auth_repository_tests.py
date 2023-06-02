import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, ANY

from bson import ObjectId
from freezegun import freeze_time
from pymongo import MongoClient

from sdk.auth.model.auth_user import AuthUser, AuthKey
from sdk.auth.model.session import DeviceSession, DeviceSessionV1
from sdk.auth.repository.mongo_auth_repository import MongoAuthRepository
from sdk.common.exceptions.exceptions import (
    UserAlreadyExistsException,
    UnauthorizedException,
    DeviceSessionDoesNotExistException,
    UserAlreadySignedOutException,
)
from sdk.common.utils import inject
from sdk.common.utils.common_functions_utils import escape

MONGO_AUTH_REPO_PATH = "sdk.auth.repository.mongo_auth_repository"
USER_COLLECTION = MongoAuthRepository.USER_COLLECTION
SESSION_COLLECTION = MongoAuthRepository.SESSION_COLLECTION
SAMPLE_DEVICE_AGENT = "Mozilla/5.0"
SAMPLE_ID = "60a20766c85cd55b38c99e12"
SAMPLE_EMAIL = "user@huma.com"
SAMPLE_PHONE_NUMBER = "+1234567890"
SAMPLE_PASSWORD = "pass1234"
USER_SAMPLE = {
    AuthUser.EMAIL: SAMPLE_EMAIL,
}

MOCK_MONGO_CLIENT = MagicMock()
MOCK_DB = MagicMock()


class MongoAuthRepositoryTestCase(unittest.TestCase):
    def setUp(self):
        def bind_and_configure(binder):
            binder.bind(MongoClient, MagicMock())

        inject.clear_and_configure(bind_and_configure)

        self._client = MOCK_MONGO_CLIENT
        self._db = MOCK_MONGO_CLIENT.get_database.return_value = MOCK_DB

    def tearDown(self):
        self._db.reset_mock()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test__check_existing_email(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].count_documents.return_value = 0

        email = SAMPLE_EMAIL
        query = {AuthUser.EMAIL: {"$regex": f"^{escape(email)}$", "$options": "i"}}

        auth_repo._check_existing_email(email=email)

        self._db[USER_COLLECTION].count_documents.assert_called_once_with(query)

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test__check_existing_email_exception(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].count_documents.return_value = 1

        with self.assertRaises(UserAlreadyExistsException):
            auth_repo._check_existing_email(email=SAMPLE_EMAIL)

        self._db[USER_COLLECTION].count_documents.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_create_user(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].count_documents.return_value = 0
        auth_user = AuthUser.from_dict(USER_SAMPLE)

        auth_repo.create_user(auth_user)

        self._db.get_collection.assert_called_once_with(USER_COLLECTION)
        self._db.get_collection().insert_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_get_user(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].find_one = MagicMock()

        auth_user = AuthUser.from_dict(USER_SAMPLE)

        auth_repo.get_user(auth_user)

        self._db[USER_COLLECTION].find_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_get_user_exception(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].find_one.return_value = None

        auth_user = AuthUser.from_dict(USER_SAMPLE)

        with self.assertRaises(UnauthorizedException):
            auth_repo.get_user(auth_user)

        self._db[USER_COLLECTION].find_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_register_device_session(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].update_one.return_value = MagicMock()

        session = DeviceSession(userId=SAMPLE_ID, deviceAgent=SAMPLE_DEVICE_AGENT)

        update_result = MagicMock()
        update_result.upserted_id = None
        self._db[USER_COLLECTION].update_one.return_value = update_result
        self._db[USER_COLLECTION].find_one.return_value = {DeviceSession.ID_: SAMPLE_ID}
        auth_repo.register_device_session(session=session)
        self._db[USER_COLLECTION].update_one.assert_called_once()
        self._db[USER_COLLECTION].find_one.assert_called()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_retrieve_device_sessions_by_user_id(self):
        auth_repo = MongoAuthRepository(client=self._client)
        user_id = ObjectId(SAMPLE_ID)

        self._db[SESSION_COLLECTION].find.return_value = [
            {
                DeviceSession.ID_: SAMPLE_ID,
                DeviceSession.USER_ID: SAMPLE_ID,
                DeviceSession.DEVICE_AGENT: SAMPLE_DEVICE_AGENT,
            },
        ]

        result = auth_repo.retrieve_device_sessions_by_user_id(user_id=user_id)

        self._db[SESSION_COLLECTION].find.assert_called_once()
        self.assertEqual(
            result,
            [
                DeviceSession(
                    id="60a20766c85cd55b38c99e12",
                    userId="60a20766c85cd55b38c99e12",
                    refreshToken=None,
                    deviceAgent="Mozilla/5.0",
                    updateDateTime=None,
                    createDateTime=None,
                ),
            ],
        )

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    @patch.object(DeviceSessionV1, "from_dict", MagicMock())
    def test_retrieve_device_session(self):
        auth_repo = MongoAuthRepository(client=self._client)

        session = self._db[SESSION_COLLECTION].find_one.return_value = MagicMock()
        session.update = MagicMock()
        session.from_dict = MagicMock()

        user_id = SAMPLE_ID
        device_agent = SAMPLE_DEVICE_AGENT

        options = {
            DeviceSessionV1.USER_ID: ObjectId(user_id),
            DeviceSessionV1.DEVICE_AGENT: device_agent,
        }

        auth_repo.retrieve_device_session(user_id=user_id, device_agent=device_agent)

        self._db[SESSION_COLLECTION].find_one.assert_called_once_with(options)
        session.update.assert_called_once_with(
            {DeviceSessionV1.ID: str(session.pop(DeviceSessionV1.ID_))}
        )

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_update_device_session(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].update_one.return_value = MagicMock()

        session = DeviceSession(id=SAMPLE_ID, userId=SAMPLE_ID)

        auth_repo.update_device_session(session)
        query = {"deviceAgent": None, "userId": ObjectId(SAMPLE_ID)}
        self._db[SESSION_COLLECTION].update_one.assert_called_with(query, ANY)

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_sign_out_device_session(self):
        auth_repo = MongoAuthRepository(client=self._client)

        self._db[SESSION_COLLECTION].update_one.return_value = MagicMock()
        self._db[SESSION_COLLECTION].find_one.return_value = MagicMock()

        session = MagicMock()

        auth_repo.sign_out_device_session(session=session)

        self._db[USER_COLLECTION].update_one.assert_called_once()
        self._db[USER_COLLECTION].find_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_sign_out_device_session_matched_none(self):
        auth_repo = MongoAuthRepository(client=self._client)

        self._db[SESSION_COLLECTION].update_one.return_value = MagicMock(
            matched_count=None
        )
        self._db[SESSION_COLLECTION].find_one.return_value = MagicMock()

        session = MagicMock()

        with self.assertRaises(DeviceSessionDoesNotExistException):
            auth_repo.sign_out_device_session(session=session)

        self._db[USER_COLLECTION].update_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_sign_out_device_session_modified_none(self):
        auth_repo = MongoAuthRepository(client=self._client)

        self._db[SESSION_COLLECTION].update_one.return_value = MagicMock(
            modified_count=None
        )
        self._db[SESSION_COLLECTION].find_one.return_value = MagicMock()

        session = MagicMock()

        with self.assertRaises(UserAlreadySignedOutException):
            auth_repo.sign_out_device_session(session=session)

        self._db[USER_COLLECTION].update_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    @patch(f"{MONGO_AUTH_REPO_PATH}.is_correct_password")
    def test_validate_password(self, mock_is_correct_password):
        auth_repo = MongoAuthRepository(client=self._client)

        uid: str = SAMPLE_ID
        email: str = SAMPLE_EMAIL
        password: str = SAMPLE_PASSWORD

        auth_repo.validate_password(uid=uid, email=email, password=password)

        mock_is_correct_password.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_confirm_email(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].update_one.return_value = MagicMock()

        uid: str = SAMPLE_ID
        email: str = SAMPLE_EMAIL

        auth_repo.confirm_email(uid=uid, email=email)

        self._db[USER_COLLECTION].update_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_confirm_email_exception(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].update_one.return_value = None

        uid: str = SAMPLE_ID
        email: str = SAMPLE_EMAIL

        with self.assertRaises(UnauthorizedException):
            auth_repo.confirm_email(uid=uid, email=email)

        self._db[USER_COLLECTION].update_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_confirm_phone_number(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].update_one.return_value = MagicMock()

        phone_number: str = SAMPLE_PHONE_NUMBER

        auth_repo.confirm_phone_number(phone_number=phone_number)

        self._db[USER_COLLECTION].update_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_confirm_phone_number_exception(self):
        auth_repo = MongoAuthRepository(client=self._client)

        self._db[USER_COLLECTION].update_one.return_value = None

        phone_number: str = SAMPLE_PHONE_NUMBER

        with self.assertRaises(UnauthorizedException):
            auth_repo.confirm_phone_number(phone_number=phone_number)

        self._db[USER_COLLECTION].update_one.assert_called_once()

    @freeze_time("2012-01-14")
    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_change_password(self):
        auth_repo = MongoAuthRepository(client=self._client)

        email = SAMPLE_EMAIL
        password = SAMPLE_PASSWORD
        previous_passwords = []

        query = {
            AuthUser.EMAIL: email,
        }
        new_data = {
            AuthUser.UPDATE_DATE_TIME: datetime.utcnow(),
            AuthUser.HASHED_PASSWORD: password,
            AuthUser.PASSWORD_UPDATE_DATE_TIME: datetime.utcnow(),
            AuthUser.PREVIOUS_PASSWORDS: previous_passwords,
        }

        auth_repo.change_password(email=email, password=password, previous_passwords=[])

        self._db[USER_COLLECTION].update_one.assert_called_once_with(
            query, {"$set": new_data}
        )

    @freeze_time("2012-01-14")
    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_change_password_exception(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].update_one.return_value = None

        email = SAMPLE_EMAIL
        password = SAMPLE_PASSWORD
        previous_passwords = []

        query = {
            AuthUser.EMAIL: email,
        }
        new_data = {
            AuthUser.UPDATE_DATE_TIME: datetime.utcnow(),
            AuthUser.HASHED_PASSWORD: password,
            AuthUser.PASSWORD_UPDATE_DATE_TIME: datetime.utcnow(),
            AuthUser.PREVIOUS_PASSWORDS: previous_passwords,
        }

        with self.assertRaises(UnauthorizedException):
            auth_repo.change_password(
                email=email, password=password, previous_passwords=[]
            )

        self._db[USER_COLLECTION].update_one.assert_called_once_with(
            query, {"$set": new_data}
        )

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_set_auth_attributes(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].update_one.return_value = MagicMock()

        uid: str = SAMPLE_ID
        email: str = SAMPLE_EMAIL
        password: str = SAMPLE_PASSWORD

        auth_repo.set_auth_attributes(uid=uid, email=email, password=password)

        self._db[USER_COLLECTION].update_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_set_auth_attributes_exception(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].update_one.return_value = None

        uid: str = SAMPLE_ID
        email: str = SAMPLE_EMAIL
        password: str = SAMPLE_PASSWORD

        with self.assertRaises(UnauthorizedException):
            auth_repo.set_auth_attributes(uid=uid, email=email, password=password)

        self._db[USER_COLLECTION].update_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_check_phone_number_exists(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].find_one.return_value = MagicMock()

        phone_number: str = SAMPLE_PHONE_NUMBER

        auth_repo.check_phone_number_exists(phone_number=phone_number)

        self._db[USER_COLLECTION].find_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_check_phone_number_exists_exception(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].find_one.return_value = None

        phone_number: str = SAMPLE_PHONE_NUMBER

        with self.assertRaises(UnauthorizedException):
            auth_repo.check_phone_number_exists(phone_number=phone_number)

        self._db[USER_COLLECTION].find_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_delete_user(self):
        auth_repo = MongoAuthRepository(client=self._client)

        user_id = SAMPLE_ID

        auth_repo.delete_user(user_id=user_id)

        self._db[USER_COLLECTION].delete_one.assert_called_once()
        self._db[SESSION_COLLECTION].delete_many.assert_called_once()

    @freeze_time("2012-01-14")
    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_create_auth_keys(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].update_one.return_value = MagicMock()

        user_id = SAMPLE_ID
        auth_key = SAMPLE_ID
        auth_identifier = SAMPLE_ID
        auth_type = AuthKey.AuthType.HAWK

        now = datetime.utcnow()
        value = {
            AuthUser.AUTH_KEYS: {
                AuthKey.AUTH_KEY: auth_key,
                AuthKey.AUTH_IDENTIFIER: auth_identifier,
                AuthKey.CREATE_DATE_TIME: now,
                AuthKey.UPDATE_DATE_TIME: now,
                AuthKey.ACTIVE: True,
                AuthKey.AUTH_TYPE: auth_type,
            }
        }
        query = {"$push": value}

        auth_repo.create_auth_keys(
            user_id=user_id,
            auth_key=auth_key,
            auth_identifier=auth_identifier,
            auth_type=auth_type,
        )

        self._db[USER_COLLECTION].update_one.assert_called_once_with(
            {AuthUser.ID_: ObjectId(user_id)}, query
        )

    @freeze_time("2012-01-14")
    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_create_auth_keys_exception(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].update_one.return_value = None

        user_id = SAMPLE_ID
        auth_key = SAMPLE_ID
        auth_identifier = SAMPLE_ID
        auth_type = AuthKey.AuthType.HAWK

        with self.assertRaises(UnauthorizedException):
            auth_repo.create_auth_keys(
                user_id=user_id,
                auth_key=auth_key,
                auth_identifier=auth_identifier,
                auth_type=auth_type,
            )

        self._db[USER_COLLECTION].update_one.assert_called_once()

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_retrieve_auth_key(self):
        auth_repo = MongoAuthRepository(client=self._client)

        result = MagicMock()
        data = {AuthUser.AUTH_KEYS: [{AuthKey.AUTH_IDENTIFIER: SAMPLE_ID}]}
        result.__getitem__.side_effect = data.__getitem__

        self._db[USER_COLLECTION].find_one.return_value = result

        user_id = SAMPLE_ID
        auth_identifier = SAMPLE_ID

        conditions = [
            {AuthUser.ID_: ObjectId(user_id)},
            {
                AuthUser.AUTH_KEYS: {
                    "$elemMatch": {AuthKey.AUTH_IDENTIFIER: auth_identifier}
                }
            },
        ]

        auth_repo.retrieve_auth_key(user_id=user_id, auth_identifier=auth_identifier)

        self._db[USER_COLLECTION].find_one.assert_called_once_with({"$and": conditions})

    @patch(f"{MONGO_AUTH_REPO_PATH}.inject", MagicMock())
    def test_retrieve_auth_key_result_none(self):
        auth_repo = MongoAuthRepository(client=self._client)
        self._db[USER_COLLECTION].find_one.return_value = None

        user_id = SAMPLE_ID
        auth_identifier = SAMPLE_ID

        with self.assertRaises(UnauthorizedException):
            auth_repo.retrieve_auth_key(
                user_id=user_id, auth_identifier=auth_identifier
            )

        self._db[USER_COLLECTION].find_one.assert_called_once()


if __name__ == "__main__":
    unittest.main()
