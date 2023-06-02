from datetime import datetime
from bson import ObjectId

from pymongo.database import Database

ID_ = "_id"
ID = "id"
ROLES = "roles"
ROLE_ID = "roleId"
RESOURCE = "resource"
UPDATE_DATE_TIME = "updateDateTime"


def _get_deployment_custom_roles(db: Database) -> list[str]:
    deployment_collection = db.get_collection("deployment")
    query = {ROLES: {"$exists": True}}
    deployments = deployment_collection.find(query)
    if not deployments:
        return []
    custom_role_ids = set()
    for deployment in deployments:
        for role in deployment[ROLES]:
            role_id = str(role.get(ID, ""))
            if ObjectId.is_valid(role_id):
                custom_role_ids.add(role_id)
    return list(custom_role_ids)


def _get_org_custom_roles(db: Database) -> list[str]:
    org_collection = db.get_collection("organization")
    query = {ROLES: {"$exists": True}}
    organizations = org_collection.find(query)
    if not organizations:
        return []
    custom_role_ids = set()
    for organization in organizations:
        for role in organization[ROLES]:
            role_id = str(role.get(ID, ""))
            if ObjectId.is_valid(role_id):
                custom_role_ids.add(role_id)
    return list(custom_role_ids)


def _clear_user_roles(
    db: Database, org_custom_roles: list[str], deployment_custom_roles: list[str]
):
    user_collection = db.get_collection("user")
    custom_roles_user_pipeline = _get_users_with_custom_role_pipeline()
    affected_users = list(user_collection.aggregate(custom_roles_user_pipeline))
    for user in affected_users:
        roles: list = user.get(ROLES, [])
        initial_roles = roles[:]
        for role in list(roles):
            role_id = role.get(ROLE_ID)
            is_custom = ObjectId.is_valid(role_id)
            if not is_custom:
                continue
            resource = role.get(RESOURCE)
            if "deployment" in resource and role_id not in deployment_custom_roles:
                roles.remove(role)
            elif "organization" in resource and role_id not in org_custom_roles:
                roles.remove(role)
        if roles != initial_roles:
            user[ROLES] = roles
            user[UPDATE_DATE_TIME] = datetime.utcnow()
            user_collection.update_one({ID_: user[ID_]}, {"$set": user})
    print(f"Done. Affected users: {len(affected_users)}")


def _get_users_with_custom_role_pipeline():
    return [
        {"$addFields": {"customRoles": "$roles"}},
        {"$unwind": {"path": "$customRoles"}},
        {
            "$match": {"$expr": {"$eq": [{"$strLenCP": "$customRoles.roleId"}, 24]}},
        },
        {"$addFields": {"objId": {"$toObjectId": "$customRoles.roleId"}}},
        {
            "$lookup": {
                "from": "deployment",
                "localField": "objId",
                "foreignField": "roles.id",
                "as": "deployment",
            }
        },
        {
            "$lookup": {
                "from": "organization",
                "localField": "objId",
                "foreignField": "roles.id",
                "as": "organization",
            }
        },
        {"$unwind": {"path": "$deployment", "preserveNullAndEmptyArrays": True}},
        {"$unwind": {"path": "$organization", "preserveNullAndEmptyArrays": True}},
        {"$match": {"deployment": None, "organization": None}},
    ]


def clear_roles(db: Database):
    org_custom_roles = _get_org_custom_roles(db)
    deployment_custom_roles = _get_deployment_custom_roles(db)
    _clear_user_roles(db, org_custom_roles, deployment_custom_roles)
