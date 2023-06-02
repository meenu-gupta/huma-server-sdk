import sys
from collections import defaultdict
from typing import Iterable

from bson import ObjectId
from pymongo import MongoClient

DB_NAME = ""
url = ""

if not url:
    raise RuntimeError(
        "MongoDB url is not provided. Please provide mongoDB url at the beginning of the script."
    )


mongo_client = MongoClient(url)
db = mongo_client.get_database(DB_NAME)


def get_affected_users() -> list[dict]:
    condition = {
        "root.emailVerified": False,
        "root.hashedPassword": {"$exists": True},
        "root.email": {"$exists": True},
    }
    pipeline = [
        {"$match": {"roles.roleId": "User"}},
        {"$project": {"_id": 1, "email": 1, "roles": 1}},
        {
            "$lookup": {
                "from": "authuser",
                "localField": "_id",
                "foreignField": "_id",
                "as": "root",
            }
        },
        {"$match": condition},
        {"$unwind": {"path": "$root"}},
    ]

    return list(db.user.aggregate(pipeline))


def extract_deployment_id_from_users(users: list[dict]) -> dict[str, list]:
    """returns {deploymentId: [User]}"""
    dep_user_dict = defaultdict(list)
    for u in users:
        roles = u.get("roles")
        if not roles:
            continue

        deployment_id = roles[0]["resource"].split("/")[-1]
        if deployment_id and deployment_id:
            dep_user_dict[deployment_id].append(u)

    return dep_user_dict


def get_deployments(ids: Iterable[str]):
    yield from db.deployment.find(
        {
            "_id": {"$in": [ObjectId(i) for i in ids]},
            "name": {"$nin": ["Fenland Study", "Fenland"]},
        },
        {"name": 1},
    )


def fix_affected_users(ids: set[ObjectId]):
    result = db.authuser.update_many(
        {"_id": {"$in": list(ids)}},
        {"$set": {"emailVerified": True}},
    )
    if not result.modified_count:
        print("No users were updated")

    print(f"Fixed {result.modified_count} users")


def ask_permission_for(callback):
    msg = "Fix all affected users? [Y|N]: "

    try:
        answer = input(msg).lower()
        if answer in ["n", "no", "not", "nope"]:
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        print()
        print("Aborted.")
        sys.exit(0)

    callback()


if __name__ == "__main__":
    print()
    users = get_affected_users()
    affected_user_ids = {user["_id"] for user in users}
    if not affected_user_ids:
        print("No affected users. We are safe!")
        sys.exit(0)

    print(f"Found {len(users)} affected users.")
    ids_dict = extract_deployment_id_from_users(users)
    deployments = get_deployments(ids_dict.keys())
    print("Affected Deployments:")
    for dep in deployments:
        print("\t", dep["name"])
        for user in ids_dict[str(dep["_id"])]:
            print("\t\t", user["root"].get("email", "unknown"), f"- {user['_id']}")
        print()

    ask_permission_for(lambda: fix_affected_users(affected_user_ids))
