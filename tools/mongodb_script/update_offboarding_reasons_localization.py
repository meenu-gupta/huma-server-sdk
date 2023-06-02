import logging

from pymongo.database import Database

from extensions.deployment.models.deployment import ReasonDetails

logger = logging.getLogger(__name__)

ID_ = "_id"
FEATURES = "features"
OFFBOARDING_REASONS = "offBoardingReasons"
REASONS = "reasons"
REASONS_PATH = f"{FEATURES}.{OFFBOARDING_REASONS}.{REASONS}"
ORDER = "order"
DISPLAY_NAME = "displayName"
DEPLOYMENT_ID = "deploymentId"
DETAILS_OFFBOARDED_PATH = "boardingStatus.detailsOffBoarded"
RESOURCE_PATH = "roles.resource"


class InitialReasonDetails:

    COMPLETED_TREATMENT: str = "Completed treatment"
    DECEASED: str = "Deceased"
    LOST_TO_FOLLOW_UP: str = "Lost to follow-up"
    MONITORING_INAPPROPRIATE: str = "Monitoring inappropriate"
    NO_LONGER_NEEDS_MONITORING: str = "No longer needs monitoring"
    RECOVERED: str = "Recovered"


initial_config = [
    {ORDER: 1, DISPLAY_NAME: InitialReasonDetails.COMPLETED_TREATMENT},
    {ORDER: 2, DISPLAY_NAME: InitialReasonDetails.DECEASED},
    {ORDER: 3, DISPLAY_NAME: InitialReasonDetails.LOST_TO_FOLLOW_UP},
    {ORDER: 4, DISPLAY_NAME: InitialReasonDetails.MONITORING_INAPPROPRIATE},
    {
        ORDER: 5,
        DISPLAY_NAME: InitialReasonDetails.NO_LONGER_NEEDS_MONITORING,
    },
    {ORDER: 6, DISPLAY_NAME: InitialReasonDetails.RECOVERED},
]


localization = {
    InitialReasonDetails.COMPLETED_TREATMENT: ReasonDetails.COMPLETED_TREATMENT,
    InitialReasonDetails.DECEASED: ReasonDetails.DECEASED,
    InitialReasonDetails.LOST_TO_FOLLOW_UP: ReasonDetails.LOST_TO_FOLLOW_UP,
    InitialReasonDetails.MONITORING_INAPPROPRIATE: ReasonDetails.MONITORING_INAPPROPRIATE,
    InitialReasonDetails.NO_LONGER_NEEDS_MONITORING: ReasonDetails.NO_LONGER_NEEDS_MONITORING,
    InitialReasonDetails.RECOVERED: ReasonDetails.RECOVERED,
}


def update_offboarding_localizations(db: Database, default_reasons: dict):
    collection = db.get_collection("deployment")
    affected_query = {REASONS_PATH: {"$eq": initial_config}}
    affected_deployments = collection.find(affected_query)
    if not affected_deployments:
        return
    affected_deployments_ids = [
        str(deployment[ID_]) for deployment in affected_deployments
    ]

    logger.warning(f"Total affected deployments: {len(affected_deployments_ids)}")
    logger.warning(f"Affected deployment IDs: {affected_deployments_ids}")

    not_default_reasons_query = {REASONS_PATH: {"$exists": True, "$ne": initial_config}}
    deployments_with_reasons = collection.find(not_default_reasons_query)
    not_default_reason_deployments_details = {
        str(deployment[ID_]): deployment[FEATURES][OFFBOARDING_REASONS][REASONS]
        for deployment in deployments_with_reasons
    }
    logger.warning(
        f"Deployments with not default reasons: {len(not_default_reason_deployments_details)}"
    )
    logger.warning(f"Details: {not_default_reason_deployments_details}")

    update_query = {"$set": {REASONS_PATH: default_reasons}}
    update_result = collection.update_many(affected_query, update_query)
    logger.info(f"{update_result.modified_count} deployments updated")
    update_affected_users(db, affected_deployments_ids)
    logger.info("Done")


def update_affected_users(db: Database, deployment_ids: list[str]):
    collection = db.get_collection("user")
    user_role_resource = [f"deployment/{d_id}" for d_id in deployment_ids]
    query = {
        RESOURCE_PATH: {"$in": user_role_resource},
        DETAILS_OFFBOARDED_PATH: {"$in": list(localization.keys())},
    }
    affected_users_count = collection.find(query).count()
    logger.warning(f"Affected users: {affected_users_count}")
    if not affected_users_count:
        return

    for reason in initial_config:
        reason_name = reason[DISPLAY_NAME]
        query = {
            RESOURCE_PATH: {"$in": user_role_resource},
            DETAILS_OFFBOARDED_PATH: reason_name,
        }
        localize_key = localization.get(reason_name)
        update_query = {"$set": {DETAILS_OFFBOARDED_PATH: localize_key}}
        affected_users = collection.update_many(query, update_query)
        logger.warning(
            f'Reason: "{reason_name}". Affected users: {affected_users.modified_count}'
        )
