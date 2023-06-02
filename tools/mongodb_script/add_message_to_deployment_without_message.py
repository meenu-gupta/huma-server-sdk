import logging
from extensions.deployment.models.deployment import Deployment, Features, Messaging

from pymongo.database import Database

from sdk.inbox.models.message import Message
from sdk.inbox.repo.models.mongo_message import MongoMessageDocument

logger = logging.getLogger(__name__)

DEPLOYMENT_COLLECTION = Deployment.__name__.lower()
INBOX_COLLECTION = MongoMessageDocument.INBOX_COLLECTION
ENABLED_KEY = f"{Deployment.FEATURES}.{Features.MESSAGING}.{Messaging.ENABLED}"
MESSAGES_KEY = f"{Deployment.FEATURES}.{Features.MESSAGING}.{Messaging.MESSAGES}"
ID_ = "_id"


def set_predefined_message_for_deployment_without_message(
    db: Database, default_message: list[str]
):
    deployment = db.get_collection(DEPLOYMENT_COLLECTION)
    affected_query = {ENABLED_KEY: True, MESSAGES_KEY: {"$in": [None, []]}}

    affected_deployments = deployment.find(affected_query)
    if not affected_deployments:
        return

    affected_deployments_ids = [
        str(deployment[ID_]) for deployment in affected_deployments
    ]

    logger.warning(f"Total affected deployments: {len(affected_deployments_ids)}")
    logger.warning(f"Affected deployment IDs: {affected_deployments_ids}")

    update_result = deployment.update_many(
        filter=affected_query,
        update={"$set": {MESSAGES_KEY: default_message}},
    )
    logger.info(f"{update_result.modified_count} deployments updated")


def set_default_custom_flag_for_messages(db: Database):
    logger.info("Updating inbox messages with no custom flag field")
    collection = db.get_collection(INBOX_COLLECTION)
    search_query = {Message.CUSTOM: None}
    update_query = {"$set": {Message.CUSTOM: False}}
    result = collection.update_many(search_query, update_query)
    logger.info(f"Updated {result.modified_count} documents")
