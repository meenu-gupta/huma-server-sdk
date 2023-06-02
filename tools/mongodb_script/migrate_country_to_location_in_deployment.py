import csv
import logging

from os import path
from pymongo.database import Database

from extensions.deployment.models.deployment import Location

logger = logging.getLogger(__name__)


DEPLOYMENT = "deployment"
COUNTRY = "country"
ID = "_id"
CAPITAL_NAME = "CapitalName"
LOCATION = "location"

here = path.abspath(path.dirname(__file__))
data_dir = f"{here}/data"
csv_file_path = f"{data_dir}/country-capitals.csv"


def move_country_to_location(db: Database):
    deployment_collection = db.get_collection(name=DEPLOYMENT)
    filter_query = {f"country": {"$exists": True}}
    deployments = deployment_collection.find(filter_query)
    logger.warning(f"{deployments.count()} deployments affected")
    modified_count = 0

    for deployment in deployments:
        deployment_id = deployment.get(ID)

        country = deployment.get(COUNTRY)
        with open(csv_file_path) as csv_file:
            users_data = csv.DictReader(csv_file)
            for row in users_data:
                if row["CountryName"] != country:
                    continue

                location = Location.from_dict(
                    {
                        Location.COUNTRY: country,
                        Location.COUNTRY_CODE: row["CountryCode"],
                        Location.CITY: row[CAPITAL_NAME],
                        Location.LATITUDE: float(row["CapitalLatitude"]),
                        Location.LONGITUDE: float(row["CapitalLongitude"]),
                        Location.ADDRESS: f"{row[CAPITAL_NAME]}, {country}",
                    }
                )
                location = location.to_dict(include_none=False)

                result = deployment_collection.update_one(
                    {ID: deployment_id},
                    {"$set": {LOCATION: location}},
                )
                modified_count += result.modified_count
                break

    logger.info(f"{modified_count} deployments updated")
