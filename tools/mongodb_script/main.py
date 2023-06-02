import argparse
import os
import sys

import pymongo as pymongo
import csv

from pymongo.database import Database

here = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(here, "../..")))

from tools.mongodb_script.models import FileData, Row

USER_COLLECTION = "user"
FIELD_NAME = "fenlandCohortId"
FENLAND_ID_NOT_FOUND_TEMPLATE = "Fenland ID not found for user %s. Email or Phone: %s; Sign up: %s"


def build_query(deployment_id):
    return {"roles.resource": f"deployment/{deployment_id}", FIELD_NAME: None}


def get_database(url: str, db_name: str):
    client = pymongo.MongoClient(url)
    return client.get_database(db_name)


def read_file_data(file_path: str) -> FileData:
    with open(file_path, newline="") as file:
        file_data = csv.reader(file, delimiter=",")
        # skip headers
        next(file_data)
        return FileData([Row(row) for row in file_data])


class DatabasePatcher:
    def __init__(self, database: Database, file_path: str, deployment_id: str):
        self.collection = database.get_collection(USER_COLLECTION)
        self.deployment_id = deployment_id
        self.file_data = read_file_data(file_path)

    def patch(self):
        users = list(self.collection.find(build_query(self.deployment_id)))
        updated_count = self.update_users(users)
        print(f"Updated {updated_count} users.")
        print(f"{len(users) - updated_count} without fenland ID were not updated.")

    def update_users(self, users: list[dict]) -> int:
        updated_users_count = 0
        for user in users:
            user_id = user.get("_id")
            fenland_id = self.file_data.get_fenland_id(str(user_id))
            if not fenland_id:
                #self.show_error_message(user)
                print(
                    user["_id"],
                )
                continue
            self.collection.update_one(
                {"_id": user_id},
                {"$set": {FIELD_NAME: fenland_id}}
            )
            updated_users_count += 1
        return updated_users_count

    @staticmethod
    def show_error_message(user):
        error_message = FENLAND_ID_NOT_FOUND_TEMPLATE % (
            user["_id"],
            user.get("email", None) or user.get("phoneNumber", None),
            str(user.get("createDateTime")),
        )
        print(error_message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FenlandId Patcher")
    parser.add_argument("--url", type=str, help="MongoDB url")
    parser.add_argument("--db", type=str, help="Database name")
    parser.add_argument("--deployment", type=str, help="Deployment Id")
    parser.add_argument("--path", type=str, help="Absolute path to a file")

    args = parser.parse_args()
    patcher = DatabasePatcher(
        database=get_database(args.url, args.db), file_path=args.path, deployment_id=args.deployment
    )
    patcher.patch()
