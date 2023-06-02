from bson import ObjectId
from pymongo import MongoClient, WriteConcern
from pymongo.read_concern import ReadConcern

from sdk.common.utils.common_functions_utils import escape

# CHANGEME
url = "mongodb+srv://ppmaintenanceuser:<password>@hu-europe-west2-prod.b7d74.gcp.mongodb.net"

# CHANGEME
db_name = "pp_eu_prod"
mongo_client = MongoClient(url)
db = mongo_client.get_database(db_name)


def ask_for_agreement(deployment_name: str):
    answer = input(
        f"Are you sure you want to delete devices for {deployment_name} deployment? [Y|N]: "
    )
    if answer.lower() in ["y", "yes", "ok", ""]:
        return True
    return False


def lookup_deployment(search: str = None, deployment_id: str = None) -> dict:
    d = db.get_collection("deployment")
    if search:
        result = d.find({"name": {"$regex": escape(search), "$options": "i"}})
    elif deployment_id:
        result = d.find_one({"_id": ObjectId(deployment_id)})
        return result
    else:
        raise NotImplementedError

    deployments = []
    for i, elem in enumerate(result):
        print(f"\n\tNumber: {i}\n\tName:\t{elem['name']}\n\tID:\t{elem['_id']}\n")
        deployments.append(elem)

    if deployments:
        choice = int(input("Enter which deployment number: "))
        return deployments[choice]


def delete_devices(deployment_id: str):
    d = db.get_collection("user")
    d2 = db.get_collection("device")
    resource = f"deployment/{deployment_id}"
    result = d.find({"roles": {"roleId": "User", "resource": resource}})
    users = list(result)
    print(f"{len(users)} users found. Deleting devices...")
    count = 0
    with mongo_client.start_session() as session:
        with session.start_transaction(
            read_concern=ReadConcern("snapshot"),
            write_concern=WriteConcern("majority", wtimeout=1000),
        ):
            for user in users:
                res = d2.delete_many({"userId": user["_id"]}, session=session)
                count += res.deleted_count

    print(f"[+] Done. {count} records were deleted.")


def main():
    deployment = None
    while not deployment:
        search = input("Enter deployment search term: ")

        if ObjectId.is_valid(search):
            deployment = lookup_deployment(deployment_id=search)
        else:
            deployment = lookup_deployment(search)

        if deployment and ask_for_agreement(deployment["name"]):
            delete_devices(str(deployment["_id"]))


if __name__ == "__main__":
    main()
