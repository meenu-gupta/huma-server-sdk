import logging

from pymongo.database import Database

logger = logging.getLogger(__name__)

LABELS = "labels"
FEATURE_LABELS = "features.labels"
ID = "_id"
FEATURES = "features"
ENABLED = "enabled"
DEPLOYMENT = "deployment"


def move_labels_from_feature_to_deployment_level(db: Database):

    deployment_collection = db.get_collection(name=DEPLOYMENT)
    filter_query = {f"{FEATURES}.{LABELS}": {"$exists": True}}
    deployments = deployment_collection.find(filter_query)
    logger.warning(f"{deployments.count()} deployments affected")
    modified_count = 0
    for deployment in deployments:
        deployment_id = deployment.get(ID)
        deployment_query = {ID: deployment_id}

        existing_labels = deployment[FEATURES].get(LABELS)

        if not existing_labels or type(existing_labels) != dict:
            continue

        deployment_update = {
            FEATURE_LABELS: existing_labels.get(ENABLED, False),
            LABELS: existing_labels.get(LABELS, []),
        }

        result = deployment_collection.update_one(
            deployment_query, {"$set": deployment_update}
        )
        logger.info(f"Done Updating {deployment_id}")
        modified_count += result.modified_count

    logger.info(f"{modified_count} deployments updated")
