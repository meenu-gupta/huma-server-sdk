import argparse
from dataclasses import dataclass

import pymongo as pymongo
from pymongo.database import Database


USER_COLLECTION = "user"
DEPLOYMENT_COLLECTION = "deployment"


class CountItem:
    ROLE = "role"
    RESOURCE = "resource"
    COUNT = "count"

    def __init__(self, role, resource_id, resource_name, count):
        self.role = role
        self.resourceId = resource_id
        self.resourceName = resource_name
        self.count = count

    def list_of_items(self):
        return [self.resourceName, self.resourceId, self.role, self.count]


class DeploymentItem:
    CLINICIAN_ROLES = [
        "Admin",
        "Manager",
        "Contributor",
    ]
    USER_ROLES = [
        "User",
        "Proxy",
    ]

    def __init__(self, name, deployment_id, patients=0, clinicians=0):
        self.deployment_name = name
        self.deployment_id = deployment_id
        self.number_of_patients = patients
        self.number_of_clinicians = clinicians

    def update(self, name, count, role):
        if self.deployment_name != name:
            raise Exception("Adding to the wrong deployment")
        if role in self.USER_ROLES:
            self.number_of_patients += int(count)
        elif role in self.CLINICIAN_ROLES:
            self.number_of_clinicians += int(count)

    def list_of_items(self):
        return [
            self.deployment_name,
            self.deployment_id,
            str(self.number_of_patients),
            str(self.number_of_clinicians),
        ]


def get_database(url: str, db_name: str):
    client = pymongo.MongoClient(url)
    return client.get_database(db_name)


class UserCount:
    EXCLUDE_ROLES = [
        "Proxy",
        "Exporter",
        "IdentifiableExport",
    ]

    def __init__(self, database: Database, file_path: str):
        self.user_collection = database.get_collection(USER_COLLECTION)
        self.deployment_collection = database.get_collection(DEPLOYMENT_COLLECTION)
        self.file_path = file_path
        self.deployment, self.custom_roles = self.get_deployment_names()
        print(f"Number of deployments: {len(self.deployment)}")
        print(f"Number of custom roles: {len(self.custom_roles)}")

    def process(self):
        pipeline = self.build_pipeline()
        result = self.user_collection.aggregate(pipeline)
        result = list(result)
        print(f"Result Count: {len(result)}")
        print(result[0])
        data = self.create_data_list(result)
        data = self.convert_data_list_to_deployment_list(data)
        data.sort(key=lambda x: x.deployment_name)
        self.create_file(data)

    def convert_data_list_to_deployment_list(self, data: list[CountItem]) -> list:
        deployments: dict[str, DeploymentItem] = {
            d: DeploymentItem(self.deployment[d], d) for d in self.deployment
        }
        for item in data:
            deployments[item.resourceId].update(
                item.resourceName, item.count, item.role
            )
        return [value for value in deployments.values()]

    def get_deployment_names(self):
        result = list(
            self.deployment_collection.find(
                projection={"_id": True, "name": True, "roles": True}
            )
        )
        deployment_names = {f"deployment/{str(d['_id'])}": d["name"] for d in result}
        all_custom_roles = sum([d["roles"] for d in result if "roles" in d], [])
        custom_roles = {
            str(r["id"]): r["userType"] for r in all_custom_roles if "userType" in r
        }
        return deployment_names, custom_roles

    def create_data_list(self, result):
        data = [item for item in [self.create_item(i) for i in result] if item]
        return data

    def create_file(self, data: list[DeploymentItem]):
        content = (
            "Deployment Name, Deployment Id, Number of Patients, Number of Clinicians"
        )
        for item in data:
            content += "\n" + ",".join(item.list_of_items())
        with open(self.file_path, "w") as file:
            file.write(content)

    def create_item(self, item: dict):
        if item["_id"][CountItem.RESOURCE] not in self.deployment:
            return None

        role = item["_id"][CountItem.ROLE]
        if role in self.custom_roles:
            role = self.custom_roles[role]

        if role in self.EXCLUDE_ROLES:
            return None

        return CountItem(
            role=role,
            resource_id=item["_id"][CountItem.RESOURCE],
            resource_name=self.deployment[item["_id"][CountItem.RESOURCE]],
            count=str(item[CountItem.COUNT]),
        )

    @staticmethod
    def build_pipeline():
        return [
            {"$unwind": {"path": "$roles"}},
            {
                "$group": {
                    "_id": {"role": "$roles.roleId", "resource": "$roles.resource"},
                    "count": {"$sum": 1},
                }
            },
        ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Counting Users in the Deployments")
    parser.add_argument("--url", type=str, help="MongoDB url")
    parser.add_argument("--db", type=str, help="Database name")
    parser.add_argument("--path", type=str, help="Absolute path to a file")

    args = parser.parse_args()

    user_counter = UserCount(get_database(args.url, args.db), args.path)
    user_counter.process()
