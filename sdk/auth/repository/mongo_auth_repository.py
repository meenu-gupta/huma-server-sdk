from datetime import datetime

from bson import ObjectId
from pymongo import WriteConcern, MongoClient
from pymongo.errors import DuplicateKeyError
from pymongo.read_concern import ReadConcern

from sdk.auth.model.auth_user import (
    AuthUser,
    AuthIdentifier,
    AuthIdentifierType,
    AuthKey,
)
from sdk.auth.model.session import DeviceSession, DeviceSessionV1
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.common.exceptions.exceptions import (
    DeviceSessionDoesNotExistException,
    UserAlreadySignedOutException,
    UnauthorizedException,
    DuplicatedPhoneNumberException,
    UserAlreadyExistsException,
)
from sdk.common.utils import inject
from sdk.common.utils.common_functions_utils import escape
from sdk.common.utils.hash_utils import is_correct_password
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values, id_as_obj_id
from sdk.phoenix.config.server_config import PhoenixServerConfig


class MongoAuthRepository(AuthRepository):
    USER_COLLECTION = "authuser"
    SESSION_COLLECTION = "devicesession"

    @autoparams()
    def __init__(self, client: MongoClient):
        self._config = inject.instance(PhoenixServerConfig)
        self._database = (
            self._config.server.auth.database
            or self._config.server.adapters.mongodbDatabase.name
        )
        self._client = client
        self._db = client.get_database(
            self._database, write_concern=WriteConcern("majority", wtimeout=10000)
        )

    def _check_existing_email(self, email: str):
        query = {AuthUser.EMAIL: {"$regex": f"^{escape(email)}$", "$options": "i"}}
        count = self._db[self.USER_COLLECTION].count_documents(query)
        if count:
            raise UserAlreadyExistsException

    def create_user(self, auth_user: AuthUser, **kwargs) -> str:
        user_dict = auth_user.to_dict(ignored_fields=AuthUser.IGNORED_FIELDS)
        if auth_user.email:
            self._check_existing_email(auth_user.email)

        self.session = self._client.start_session()
        self.session.start_transaction(
            read_concern=ReadConcern("snapshot"),
            write_concern=WriteConcern("majority", wtimeout=10000),
        )
        if auth_user.id is not None:
            user_dict["_id"] = ObjectId(auth_user.id)
        return str(
            self._client.get_database(self._database)
            .get_collection(self.USER_COLLECTION)
            .insert_one(remove_none_values(user_dict), session=self.session)
            .inserted_id
        )

    def get_user(
        self, phone_number: str = None, email: str = None, uid: str = None, **kwargs
    ) -> AuthUser:
        query = {}
        if phone_number is not None:
            query[AuthUser.PHONE_NUMBER] = phone_number
        if email is not None:
            query[AuthUser.EMAIL] = {"$regex": f"^{escape(email)}$", "$options": "i"}
        if uid is not None:
            query["_id"] = ObjectId(uid)
        result = self._db[self.USER_COLLECTION].find_one(query)
        if result is None:
            raise UnauthorizedException

        user = AuthUser.from_dict(result)
        user.id = str(result["_id"])
        return user

    def register_device_session(self, session: DeviceSessionV1) -> str:
        session.updateDateTime = session.createDateTime = datetime.utcnow()
        session_dict = session.to_dict(
            ignored_fields=[
                DeviceSessionV1.CREATE_DATE_TIME,
                DeviceSessionV1.UPDATE_DATE_TIME,
            ],
            include_none=False,
        )
        find_data = {
            DeviceSessionV1.USER_ID: session_dict.pop(DeviceSessionV1.USER_ID),
            DeviceSessionV1.DEVICE_AGENT: session_dict.pop(
                DeviceSessionV1.DEVICE_AGENT
            ),
        }
        result = self._db[self.SESSION_COLLECTION].update_one(
            find_data, {"$set": session_dict}, upsert=True
        )
        if result.upserted_id:
            session_id = str(result.upserted_id)
        else:
            session_id = str(
                self._db[self.SESSION_COLLECTION].find_one(find_data)[
                    DeviceSessionV1.ID_
                ]
            )
        return session_id

    @id_as_obj_id
    def retrieve_device_sessions_by_user_id(
        self, user_id: ObjectId, only_enabled: bool = True
    ) -> list[DeviceSession]:
        options = {DeviceSession.USER_ID: user_id}
        if only_enabled:
            options.update({DeviceSession.REFRESH_TOKEN: {"$ne": None}})

        sessions = self._db[self.SESSION_COLLECTION].find(options)
        result = []
        for session in sessions:
            session.update({DeviceSession.ID: str(session.pop(DeviceSession.ID_))})
            result.append(DeviceSession.from_dict(session))
        return result

    @id_as_obj_id
    def retrieve_device_session(
        self,
        user_id: str,
        device_agent: str = None,
        refresh_token: str = None,
        check_is_active: bool = False,
    ) -> DeviceSessionV1:
        options = {
            DeviceSessionV1.USER_ID: user_id,
        }
        if device_agent:
            options[DeviceSessionV1.DEVICE_AGENT] = device_agent
        if refresh_token:
            options[DeviceSessionV1.REFRESH_TOKEN] = refresh_token
        if check_is_active:
            options[DeviceSessionV1.IS_ACTIVE] = True
        session = self._db[self.SESSION_COLLECTION].find_one(options)
        if not session:
            raise DeviceSessionDoesNotExistException
        session.update({DeviceSessionV1.ID: str(session.pop(DeviceSessionV1.ID_))})
        return DeviceSessionV1.from_dict(session)

    def update_device_session(self, session: DeviceSession):
        session_dict = session.to_dict(include_none=False)
        session_dict[DeviceSession.UPDATE_DATE_TIME] = datetime.utcnow()
        query = {
            DeviceSession.DEVICE_AGENT: session.deviceAgent,
            DeviceSession.USER_ID: ObjectId(session.userId),
        }
        _ = self._db[self.SESSION_COLLECTION].update_one(
            query,
            {"$set": remove_none_values(session_dict)},
        )

    def update_device_session_v1(
        self, session: DeviceSessionV1, refresh_token: str = None
    ):
        session_dict = session.to_dict(include_none=False)
        session_dict[DeviceSessionV1.UPDATE_DATE_TIME] = datetime.utcnow()
        query = {
            DeviceSessionV1.DEVICE_AGENT: session.deviceAgent,
            DeviceSessionV1.USER_ID: ObjectId(session.userId),
            DeviceSessionV1.REFRESH_TOKEN: refresh_token,
        }
        result = self._db[self.SESSION_COLLECTION].update_one(
            remove_none_values(query),
            {"$set": remove_none_values(session_dict)},
        )
        if not result.matched_count:
            raise DeviceSessionDoesNotExistException

    def sign_out_device_session(self, session: DeviceSession) -> str:
        session_dict = session.to_dict(include_none=False)
        result = self._db[self.SESSION_COLLECTION].update_one(
            session_dict, {"$set": {DeviceSession.REFRESH_TOKEN: None}}
        )
        if not result.matched_count:
            raise DeviceSessionDoesNotExistException
        if not result.modified_count:
            raise UserAlreadySignedOutException

        result = self._db[self.SESSION_COLLECTION].find_one(session_dict)
        return str(result[DeviceSession.ID_])

    def sign_out_device_session_v1(self, session: DeviceSessionV1) -> str:
        session_dict = session.to_dict(include_none=False)

        result = self._db[self.SESSION_COLLECTION].update_one(
            session_dict,
            {"$set": {DeviceSessionV1.IS_ACTIVE: False}},
        )
        if not result.matched_count:
            raise DeviceSessionDoesNotExistException
        if not result.modified_count:
            raise UserAlreadySignedOutException

        result = self._db[self.SESSION_COLLECTION].find_one(
            {**session_dict, DeviceSessionV1.IS_ACTIVE: False}
        )
        return str(result[DeviceSessionV1.ID_])

    def commit_transactions(self):
        if self.session is not None:
            self.session.commit_transaction()

    def cancel_transactions(self):
        if self.session is not None:
            self.session.abort_transaction()

    def validate_password(self, password: str, email: str = None, uid: str = None):
        user = self.get_user(email=email, uid=uid)
        return is_correct_password(user.hashedPassword, password)

    def confirm_email(self, email: str, uid: str = None):
        query = {AuthUser.EMAIL: email}
        if uid:
            query[AuthUser.ID_] = ObjectId(uid)
        new_data = {
            AuthUser.UPDATE_DATE_TIME: datetime.utcnow(),
            AuthUser.EMAIL_VERIFIED: True,
        }
        res = self._db[self.USER_COLLECTION].update_one(
            query, {"$set": new_data}, session=self.session
        )
        if not res:
            raise UnauthorizedException

    def confirm_phone_number(self, phone_number: str):
        query = {AuthUser.PHONE_NUMBER: phone_number}
        new_data = {
            AuthUser.UPDATE_DATE_TIME: datetime.utcnow(),
            AuthUser.PHONE_NUMBER_VERIFIED: True,
        }
        res = self._db[self.USER_COLLECTION].update_one(query, {"$set": new_data})
        if not res:
            raise UnauthorizedException

    def change_password(self, password: str, email: str, previous_passwords: list[str]):
        query = {AuthUser.EMAIL: email}
        new_data = {
            AuthUser.UPDATE_DATE_TIME: datetime.utcnow(),
            AuthUser.HASHED_PASSWORD: password,
            AuthUser.PASSWORD_UPDATE_DATE_TIME: datetime.utcnow(),
            AuthUser.PREVIOUS_PASSWORDS: previous_passwords,
        }
        res = self._db[self.USER_COLLECTION].update_one(query, {"$set": new_data})
        if not res:
            raise UnauthorizedException

    def set_auth_attributes(
        self,
        uid: str,
        password: str = None,
        email: str = None,
        mfa_identifiers: list = None,
        mfa_enabled: bool = None,
    ):
        query = {AuthUser.ID_: ObjectId(uid)}
        now = datetime.utcnow()
        values_to_update = remove_none_values(
            {
                AuthUser.HASHED_PASSWORD: password,
                AuthUser.EMAIL: email,
                AuthUser.MFA_IDENTIFIERS: mfa_identifiers,
                AuthUser.UPDATE_DATE_TIME: now,
                AuthUser.MFA_ENABLED: mfa_enabled,
            }
        )
        if password:
            values_to_update[AuthUser.PASSWORD_UPDATE_DATE_TIME] = now
            values_to_update[AuthUser.PASSWORD_CREATE_DATE_TIME] = now
        try:
            res = self._db[self.USER_COLLECTION].update_one(
                query, {"$set": values_to_update}
            )
        except DuplicateKeyError as e:
            if "phoneNumber" in str(e):
                raise DuplicatedPhoneNumberException
            else:
                raise UserAlreadyExistsException
        if not res:
            raise UnauthorizedException

    def check_phone_number_exists(self, phone_number: str):
        match_query = {
            AuthIdentifier.TYPE: AuthIdentifierType.PHONE_NUMBER,
            AuthIdentifier.VALUE: phone_number,
        }
        query = {
            "$or": [
                {AuthUser.PHONE_NUMBER: phone_number},
                {AuthUser.MFA_IDENTIFIERS: {"$elemMatch": match_query}},
            ]
        }
        result = self._db[self.USER_COLLECTION].find_one(query)
        if result is None:
            raise UnauthorizedException

    @id_as_obj_id
    def delete_user(self, user_id: str):
        self.session = self._client.start_session()
        self.session.start_transaction(
            read_concern=ReadConcern("snapshot"),
            write_concern=WriteConcern("majority", wtimeout=10000),
        )
        self._db[self.USER_COLLECTION].delete_one(
            {AuthUser.ID_: user_id}, session=self.session
        )
        self._db[self.SESSION_COLLECTION].delete_many(
            {DeviceSession.USER_ID: user_id}, session=self.session
        )

    @id_as_obj_id
    def create_auth_keys(
        self,
        user_id: str,
        auth_key: str,
        auth_identifier: str,
        auth_type: AuthKey.AuthType,
    ):
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
        result = self._db[self.USER_COLLECTION].update_one(
            {AuthUser.ID_: user_id}, query
        )
        if not result:
            raise UnauthorizedException

    @id_as_obj_id
    def retrieve_auth_key(self, user_id: str, auth_identifier: str):
        conditions = [
            {AuthUser.ID_: user_id},
            {
                AuthUser.AUTH_KEYS: {
                    "$elemMatch": {AuthKey.AUTH_IDENTIFIER: auth_identifier}
                }
            },
        ]

        result = self._db[self.USER_COLLECTION].find_one({"$and": conditions})
        if not result:
            raise UnauthorizedException

        auth_keys = result[AuthUser.AUTH_KEYS]
        auth_key = next(
            filter(lambda x: x[AuthKey.AUTH_IDENTIFIER] == auth_identifier, auth_keys),
            None,
        )
        if not auth_key:
            raise UnauthorizedException

        return auth_key

    @id_as_obj_id
    def validate_device_token(self, device_token: str, user_id: str):
        query = {"_id": user_id}
        result = self._db[self.USER_COLLECTION].find_one(query)
        if result is None:
            raise UnauthorizedException

        user: AuthUser = AuthUser.from_dict(result)
        identifier = user.get_mfa_identifier(
            AuthIdentifierType.DEVICE_TOKEN, device_token
        )
        if not identifier:
            raise UnauthorizedException
