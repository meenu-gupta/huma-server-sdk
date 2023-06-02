#!/usr/bin/env python

import http.client
import logging
import os
import sys

import fire
import pymongo
from bson import ObjectId
from pymongo.errors import PyMongoError


here = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(here, "../..")))

from sdk.common.utils.url_utils import clean_password_from_url
from extensions.utils import generate_code

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


def delete_user(host_url, token_str, user_id, secure=False):
    if secure:
        conn = http.client.HTTPSConnection(host_url)
    else:
        conn = http.client.HTTPConnection(host_url)

    payload = ""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token_str}",
    }

    conn.request(
        "DELETE", f"/api/extensions/v1beta/user/{user_id}/delete-user", payload, headers
    )

    res = conn.getresponse()
    if res.status - 400 >= 0:
        print(f"- Can NOT delete user {user_id}")
        return

    print(f"+ user {user_id} deleted")


class RemoveUser(object):
    def __init__(self, url, secure=False):
        self.url = url
        self.secure = secure

    def remove_all(self):
        with open("users.txt", "r") as fd:
            users = [line.strip() for line in fd.readlines()]
            print(users[0])

        with open("token", "r") as fd:
            token = fd.readline().strip()

        for user in users:
            delete_user(self.url, token, user, secure=self.secure)

    def de_identify(self, mongo_url, database):
        mongodb_db_client = pymongo.MongoClient(
            mongo_url, serverSelectionTimeoutMS=10 * 1000
        )

        # testing the connection before connecting
        db = mongodb_db_client[database]
        result = db.command("ping").get("ok")

        safe_url = clean_password_from_url(self.url)

        if result != 1.0:
            raise PyMongoError(f"can not connect to {safe_url}")

        logger.info(f"mongodb client has been connected {safe_url}")

        users = db["user"].find({})
        index = 0
        for user in users:
            u = str(user["_id"])
            print(u)
            db["user"].update_one(
                {"_id": ObjectId(u)},
                {
                    "$set": {
                        "email": f"j{index}.smith@example.com",
                        "phoneNumber": f"+44444444{index}",
                        "givenName": "j",
                        "familyName": "smith",
                        "additionalContactDetails": {},
                    }
                },
            )
            db["authuser"].update_one(
                {"_id": ObjectId(u)},
                {
                    "$set": {
                        "email": f"j{index}.smith@example.com",
                        "displayName": "j",
                        "userAttributes.givenName": "j",
                        "userAttributes.familyName": "smith",
                        "mfaIdentifiers.0.value": "+447484889827",
                        "hashedPassword": "$2b$12$jEyU2S6GUPpsfrDpOe8wJ.wfhckFYDpsddsqlKxLM9iXTWjcGdE.u"
                    }
                },
            )
            db["econsentlog"].update_one(
                {"userId": ObjectId(u)},
                {
                    "$set": {
                        "givenName": f"j{index}",
                        "familyName": "smith",
                    }
                },
            )
            db["verificationlog"].update_many(
                {"userId": ObjectId(u)},
                {
                    "$set": {
                        "legalFirstName": f"j{index}",
                        "legalLastName": "smith",
                    }
                },
            )

            index += 1

        deps = db["deployment"].find({})
        index = 0
        for dep in deps:
            db["deployment"].update_one(
                {"_id": dep["_id"]},
                {
                    "$set": {
                        "userActivationCode": generate_code(8),
                        "managerActivationCode": generate_code(12, True),
                        "proxyActivationCode": generate_code(8),
                    }
                },
            )

            index += 1

        db.drop_collection("device")
        db.drop_collection("devicesession")
        db.drop_collection("deploymentrevision") # maybe this is not good
        db.drop_collection("invitation")

    def all_users_not_in_deployment(self, mongo_url, database, deployment_id):
        mongodb_db_client = pymongo.MongoClient(
            mongo_url, serverSelectionTimeoutMS=10 * 1000
        )

        # testing the connection before connecting
        db = mongodb_db_client[database]
        result = db.command("ping").get("ok")

        safe_url = clean_password_from_url(self.url)

        if result != 1.0:
            raise PyMongoError(f"can not connect to {safe_url}")

        logger.info(f"mongodb client has been connected {safe_url}")

        users_not_in_dep = db["user"].find(
            {"roles.resource": {"$ne": f"deployment/{deployment_id}"}}
        )

        with open("users.txt", "w") as fd:
            for u in users_not_in_dep:
                fd.write(str(u["_id"]))
                fd.write("\n")

    def check_users(self, mongo_url, database):
        with open("users.txt", "r") as fd:
            users = [line.strip() for line in fd.readlines()]
            print(users[0])

        mongodb_db_client = pymongo.MongoClient(
            mongo_url, serverSelectionTimeoutMS=10 * 1000
        )

        # testing the connection before connecting
        db = mongodb_db_client[database]
        result = db.command("ping").get("ok")

        safe_url = clean_password_from_url(self.url)

        if result != 1.0:
            raise PyMongoError(f"can not connect to {safe_url}")

        logger.info(f"mongodb client has been connected {safe_url}")

        collections = db.list_collection_names()

        for u in users:
            not_exist = True
            for col in collections:
                search_dict = {
                    "$or": [
                        {"userId": u},
                        {"userId": ObjectId(u)},
                        {"id": ObjectId(u)},
                        {"_id": ObjectId(u)},
                        {"_id": u},
                    ]
                }
                if db[col].find_one(search_dict) is not None:
                    print(f"+ User {u} exist at collection {col}")
                    not_exist = False

            if not_exist:
                print(f"- User {u} not exist")


if __name__ == "__main__":
    fire.Fire(RemoveUser)

    """
    How to run
    $ ./deleteusers.py --url localhost:3901 - remove-all
    $ ./deleteusers.py --url localhost:3901 - check-users --mongo_url mongodb://root:password123@localhost:27027 --database pp_eu_prod
    $ ./deleteusers.py --url localhost:3901 - all_users_not_in_deployment --mongo_url mongodb://root:password123@localhost:27027 --database pp_eu_prod --deployment_id 5f273e030319b4ad57b7a305
    $ ./deleteusers.py --url localhost:3901 - de-identify --mongo_url mongodb://root:password123@localhost:27027 --database pp_eu_prod
    """