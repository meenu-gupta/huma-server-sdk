import logging

from bson import ObjectId
from pymongo.database import Database

from extensions.authorization.models.user import User
from extensions.exceptions import UserDoesNotExist
from sdk.common.utils.inject import autoparams

log = logging.getLogger(__name__)


class MongoUserRepository:
    USER_COLLECTION = "user"

    @autoparams()
    def __init__(self, database: Database):
        self._db = database

    def retrieve_user_dict_by_id(self, uid: str) -> dict:
        result = self._db[self.USER_COLLECTION].find_one({User.ID_: ObjectId(uid)})

        if result is None:
            raise UserDoesNotExist

        result[User.ID_] = str(result[User.ID_])
        if result.get(User.TAGS_AUTHOR_ID):
            result[User.TAGS_AUTHOR_ID] = str(result[User.TAGS_AUTHOR_ID])

        return result
