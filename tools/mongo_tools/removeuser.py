#!/usr/bin/env python
import logging
import os
import sys
import fire
import pymongo
from bson import ObjectId
from pymongo.errors import PyMongoError

here = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(here, "../..")))

from sdk.auth.model.auth_user import AuthUser
from sdk.common.utils.url_utils import clean_password_from_url
from extensions.authorization.models.user import User

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


class RemoveUser(object):
    def __init__(
        self,
        database,
        phone=None,
        email=None,
        url="localhost:27017",
    ):
        self.database = database
        self.url = url
        self.phone = phone
        self.email = email
        if not (self.email or self.phone):
            raise RuntimeError("Phone or email should be available")

    def remove(self):
        # ~~~~~~~~
        # connecting to mongo
        mongodb_db_client = pymongo.MongoClient(
            self.url, serverSelectionTimeoutMS=10 * 1000
        )

        # testing the connection before connecting
        db = mongodb_db_client[self.database]
        result = db.command("ping").get("ok")

        safe_url = clean_password_from_url(self.url)

        if result != 1.0:
            raise PyMongoError(f"can not connect to {safe_url}")

        logger.info(f"mongodb client has been connected {safe_url}")
        logger.info(f"search for {self.phone} phone number")

        search_dict = (
            {"phoneNumber": self.phone} if self.phone else {"email": self.email}
        )

        auth_user = AuthUser.from_dict(db["authuser"].find_one(search_dict))
        print(auth_user)
        _id = auth_user.id
        user = User.from_dict(db["user"].find_one({"_id": ObjectId(_id)} or {}))
        print(user)

        if auth_user.id and (user.phoneNumber or user.email):
            answer = input("Please indicate approval: [y/n]\n")
            if not answer or answer[0].lower() != "y":
                print("You did not indicate approval\n")
                exit(1)
            logger.info(f"Removing the {self.phone or self.email}")
            db["authuser"].delete_one({"_id": ObjectId(_id)})
            db["user"].delete_one({"_id": ObjectId(_id)})
            logger.info(f"Removed {self.phone or self.email}")
        else:
            logger.info(
                f"Can NOT remove the {self.phone or self.email} as it can't find it"
            )


if __name__ == "__main__":
    fire.Fire(RemoveUser)

    """
    How to run
    $ ./removeuser.py --url mongodb://root:password123@localhost:27027 --database pp_local_dev --email milano.fili+u@gmail.com - remove
    """
