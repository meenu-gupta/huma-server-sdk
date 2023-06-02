from pymongo import MongoClient

# Replace with the database url
url = "mongodb+srv://ppapp:JkbAnz2vXANsQJ2BfEjrJbiy@hu-pre-prod-london.wjabo.gcp.mongodb.net"

# Replace with the database name
db_name = "pp_qa"
mongo_client = MongoClient(url)
db = mongo_client.get_database(db_name)

d = db.get_collection("breastfeedingupdate")


def main():
    for i in d.find():
        current_value = i["newOrWorseSymptoms"]
        if isinstance(current_value, int):
            d.update_one(
                {"_id": i["_id"], "newOrWorseSymptoms": current_value},
                {"$set": {"newOrWorseSymptoms": [current_value]}},
            )
    print("Done...")


if __name__ == "__main__":
    main()
