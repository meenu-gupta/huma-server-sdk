import csv
import datetime
import logging
import random
import string
from os import path
from typing import Tuple

from bson import ObjectId
from pymongo import MongoClient, WriteConcern
from pymongo.client_session import ClientSession
from pymongo.database import Database

from extensions.authorization.models.user import User, RoleAssignment, BoardingStatus
from extensions.dashboard.models.configuration import DeploymentLevelConfiguration
from extensions.dashboard.models.dashboard import DashboardId
from extensions.deployment.models.consent.consent_signature import ConsentSignature
from extensions.deployment.models.deployment import Deployment, OnboardingModuleConfig
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.models.econsent.econsent_section import EConsentSection
from extensions.deployment.models.status import Status
from extensions.organization.models.organization import Organization, ViewType
from extensions.organization.repository.mongo_organization_repository import (
    MongoOrganizationRepository,
)
from sdk.auth.model.auth_user import AuthUser
from sdk.common.utils.validators import utc_str_val_to_field

logger = logging.getLogger(__file__)

here = path.abspath(path.dirname(__file__))
data_dir = f"{here}/data"

db_name = "pp_integration_tests"

USER_DATA_PATH = "userDataPath"
ECONSENT_ENABLED = "econsentEnabled"
EXTRA_MODULE_CONFIGS = "extraModuleConfigs"

IN_STUDY = "In study"
ID_VERIFICATION = "ID"
CONSENTED = "Consented"

USER_COLLECTION = "user"
AUTH_USER_COLLECTION = "authuser"
ECONSENT_LOG_COLLECTION = "econsentlog"


def upload_test_gadgets_data(
    db: Database, mongo_client: MongoClient, org_id: str = None
):
    deployments_config = {
        "Deployment1": {
            USER_DATA_PATH: f"{data_dir}/Deployment1.Participants.csv",
            EXTRA_MODULE_CONFIGS: {
                Deployment.DASHBOARD_CONFIGURATION: {
                    DeploymentLevelConfiguration.TARGET_CONSENTED: 500,
                    DeploymentLevelConfiguration.TARGET_CONSENTED_MONTHLY: 30,
                    DeploymentLevelConfiguration.TARGET_COMPLETED: 120,
                },
                Deployment.ONBOARDING_CONFIGS: [
                    {
                        OnboardingModuleConfig.CONFIG_BODY: {},
                        OnboardingModuleConfig.ONBOARDING_ID: "IdentityVerification",
                        OnboardingModuleConfig.ORDER: 1,
                        OnboardingModuleConfig.STATUS: "ENABLED",
                        OnboardingModuleConfig.USER_TYPES: ["User"],
                        OnboardingModuleConfig.VERSION: 0,
                    },
                    {
                        OnboardingModuleConfig.CONFIG_BODY: {},
                        OnboardingModuleConfig.ONBOARDING_ID: "EConsent",
                        OnboardingModuleConfig.ORDER: 2,
                        OnboardingModuleConfig.STATUS: "ENABLED",
                        OnboardingModuleConfig.USER_TYPES: ["User"],
                        OnboardingModuleConfig.VERSION: 0,
                    },
                ],
            },
            ECONSENT_ENABLED: True,
        },
        "Deployment2": {
            USER_DATA_PATH: f"{data_dir}/Deployment2.Participants.csv",
            EXTRA_MODULE_CONFIGS: {
                Deployment.DASHBOARD_CONFIGURATION: {
                    DeploymentLevelConfiguration.TARGET_CONSENTED: 0,
                    DeploymentLevelConfiguration.TARGET_CONSENTED_MONTHLY: 0,
                    DeploymentLevelConfiguration.TARGET_COMPLETED: 180,
                },
                Deployment.ONBOARDING_CONFIGS: [
                    {
                        OnboardingModuleConfig.CONFIG_BODY: {},
                        OnboardingModuleConfig.ONBOARDING_ID: "IdentityVerification",
                        OnboardingModuleConfig.ORDER: 1,
                        OnboardingModuleConfig.STATUS: "ENABLED",
                        OnboardingModuleConfig.USER_TYPES: ["User"],
                        OnboardingModuleConfig.VERSION: 0,
                    },
                    {
                        OnboardingModuleConfig.CONFIG_BODY: {},
                        OnboardingModuleConfig.ONBOARDING_ID: "EConsent",
                        OnboardingModuleConfig.ORDER: 2,
                        OnboardingModuleConfig.STATUS: "ENABLED",
                        OnboardingModuleConfig.USER_TYPES: ["User"],
                        OnboardingModuleConfig.VERSION: 0,
                    },
                ],
            },
            ECONSENT_ENABLED: True,
        },
        "Deployment3": {
            USER_DATA_PATH: f"{data_dir}/Deployment3.Participants.csv",
            EXTRA_MODULE_CONFIGS: {
                Deployment.DASHBOARD_CONFIGURATION: {
                    DeploymentLevelConfiguration.TARGET_CONSENTED: 550,
                    DeploymentLevelConfiguration.TARGET_CONSENTED_MONTHLY: 33,
                    DeploymentLevelConfiguration.TARGET_COMPLETED: 200,
                },
                Deployment.ONBOARDING_CONFIGS: [
                    {
                        OnboardingModuleConfig.CONFIG_BODY: {},
                        OnboardingModuleConfig.ONBOARDING_ID: "IdentityVerification",
                        OnboardingModuleConfig.ORDER: 1,
                        OnboardingModuleConfig.STATUS: "ENABLED",
                        OnboardingModuleConfig.USER_TYPES: ["User"],
                        OnboardingModuleConfig.VERSION: 0,
                    },
                    {
                        OnboardingModuleConfig.CONFIG_BODY: {},
                        OnboardingModuleConfig.ONBOARDING_ID: "EConsent",
                        OnboardingModuleConfig.ORDER: 2,
                        OnboardingModuleConfig.STATUS: "ENABLED",
                        OnboardingModuleConfig.USER_TYPES: ["User"],
                        OnboardingModuleConfig.VERSION: 0,
                    },
                ],
            },
            ECONSENT_ENABLED: True,
        },
    }

    with mongo_client.start_session() as session:
        with session.start_transaction(
            write_concern=WriteConcern("majority", wtimeout=10000),
        ):
            return _generate_data(deployments_config, db, session, org_id)


def _generate_data(
    deployments_config: dict, db: Database, session: ClientSession, org_id: str = None
):
    created_total = 0
    econsented_total = 0
    deployments_ids = []
    for deployment_name, data_config in deployments_config.items():
        include_econsent = data_config.get(ECONSENT_ENABLED)
        econsent_id = ObjectId() if include_econsent else None
        deployment_config = data_config[EXTRA_MODULE_CONFIGS]
        deployment_id = _create_deployment(
            deployment_name, db, session, econsent_id, deployment_config
        )
        deployments_ids.append(deployment_id)

        users_data, auth_users_data, econsents_data = _generate_users_data(
            deployment_id, econsent_id, data_config
        )

        db[USER_COLLECTION].insert_many(users_data, session=session)
        db[AUTH_USER_COLLECTION].insert_many(auth_users_data, session=session)
        if econsents_data:
            db[ECONSENT_LOG_COLLECTION].insert_many(econsents_data, session=session)

        created_total += len(users_data)
        econsented_total += len(econsents_data)
        logger.warning(
            f"{len(users_data)} users have been created for deployment {deployment_id}"
        )
        logger.warning(
            f"{len(econsents_data)} users have been econsented for deployment {deployment_id}"
        )

    logger.warning(f"Total {created_total} users have been created")
    logger.warning(f"Total {econsented_total} users have been econsented")
    org_id = _create_organization(deployments_ids, db, session, org_id)
    return org_id, deployments_ids


def _create_econsent_log_dict(
    econsent_id: ObjectId, econsent_date: datetime, user_id: ObjectId
):
    return {
        EConsentLog.ID_: ObjectId(),
        EConsentLog.USER_ID: user_id,
        EConsentLog.ECONSENT_ID: econsent_id,
        EConsentLog.REVISION: 1,
        EConsentLog.SIGNATURE: {"bucket": "bucket", "key": "key", "region": "eu"},
        EConsentLog.PDF_LOCATION: {"bucket": "bucket", "key": "key", "region": "eu"},
        EConsentLog.CREATE_DATE_TIME: econsent_date,
    }


def _create_deployment(
    deployment_name: str,
    db: Database,
    session: ClientSession,
    econsent_id: ObjectId = None,
    extra_configs: dict = None,
) -> str:
    deployment_dict = {
        Deployment.ID_: ObjectId(),
        Deployment.NAME: deployment_name,
        Deployment.STATUS: Status.DEPLOYED.value,
        Deployment.COLOR: "0x007AFF",
        Deployment.CREATE_DATE_TIME: utc_str_val_to_field("2012-12-24T00:00:00.000Z"),
        Deployment.UPDATE_DATE_TIME: utc_str_val_to_field("2012-12-24T00:00:00.000Z"),
        **(extra_configs or {}),
    }
    if econsent_id:
        deployment_dict[Deployment.ECONSENT] = {
            EConsent.ID: econsent_id,
            EConsent.ENABLED: "ENABLED",
            EConsent.TITLE: "Informed consent form",
            EConsent.OVERVIEW_TEXT: "Overview",
            EConsent.CONTACT_TEXT: "Contact",
            EConsent.REVISION: 1,
            EConsent.SIGNATURE: {
                ConsentSignature.SIGNATURE_TITLE: "Signature",
                ConsentSignature.SIGNATURE_DETAILS: "Please sign",
                ConsentSignature.NAME_TITLE: "Consent",
                ConsentSignature.NAME_DETAILS: "Type your full name in text fields below",
            },
            EConsent.SECTIONS: [
                {
                    EConsentSection.TYPE: "PURPOSE",
                    EConsentSection.TITLE: "PURPOSE",
                    EConsentSection.REVIEW_DETAILS: "details",
                    EConsentSection.CONTENT_TYPE: "IMAGE",
                    EConsentSection.THUMBNAIL_URL: "https://somwhere/sample-4.jpg",
                }
            ],
        }
    result = db.get_collection("deployment").insert_one(
        deployment_dict, session=session
    )
    deployment_id = str(result.inserted_id)
    logger.warning(
        f"Deployment {deployment_name} with id {deployment_id} have been created"
    )
    return deployment_id


def _create_auth_user_dict(user_id: ObjectId, sign_up_dt: datetime, email: str):
    return {
        AuthUser.ID_: user_id,
        AuthUser.ID: str(user_id),
        AuthUser.EMAIL_VERIFIED: True,
        AuthUser.EMAIL: email,
        AuthUser.DISPLAY_NAME: "test",
        AuthUser.USER_ATTRIBUTES: {
            "familyName": "test",
            "givenName": "test",
            "dob": "1988-02-20",
            "gender": "Male",
        },
        AuthUser.CREATE_DATE_TIME: sign_up_dt,
        AuthUser.UPDATE_DATE_TIME: sign_up_dt,
    }


def _create_sample_user_dict(
    deployment_id: str,
    sign_up_dt: datetime,
    in_study: str,
    id_status: str,
    consented: str,
) -> dict:
    user_dict = {
        User.ID_: ObjectId(),
        User.GIVEN_NAME: "testUser",
        User.FAMILY_NAME: "testUser",
        User.EMAIL: _generate_random_email(),
        User.ROLES: [
            {
                RoleAssignment.ROLE_ID: "User",
                RoleAssignment.RESOURCE: f"deployment/{deployment_id}",
                RoleAssignment.USER_TYPE: "User",
            }
        ],
        User.TIMEZONE: "UTC",
        User.CREATE_DATE_TIME: sign_up_dt,
        User.UPDATE_DATE_TIME: sign_up_dt,
    }
    if in_study == "Completed":
        user_dict[User.BOARDING_STATUS] = {
            BoardingStatus.REASON_OFF_BOARDED: BoardingStatus.ReasonOffBoarded.USER_COMPLETE_ALL_TASK
        }
    if id_status == "ID verified":
        user_dict[
            User.VERIFICATION_STATUS
        ] = User.VerificationStatus.ID_VERIFICATION_SUCCEEDED.value
    if id_status == "Failed ID":
        user_dict[User.BOARDING_STATUS] = {
            BoardingStatus.REASON_OFF_BOARDED: BoardingStatus.ReasonOffBoarded.USER_FAIL_ID_VERIFICATION
        }
    if consented == "Refused Consented":
        user_dict[User.BOARDING_STATUS] = {
            BoardingStatus.REASON_OFF_BOARDED: BoardingStatus.ReasonOffBoarded.USER_UNSIGNED_EICF
        }
    if in_study == "Withdrew Consented":
        user_dict[User.BOARDING_STATUS] = {
            BoardingStatus.REASON_OFF_BOARDED: BoardingStatus.ReasonOffBoarded.USER_WITHDRAW_EICF
        }
    if in_study == "Manual Drop-off":
        user_dict[User.BOARDING_STATUS] = {
            BoardingStatus.REASON_OFF_BOARDED: BoardingStatus.ReasonOffBoarded.USER_MANUAL_OFF_BOARDED
        }
    return user_dict


def _generate_random_email() -> str:
    random_chars = "".join(random.choice(string.ascii_letters) for _ in range(10))
    return f"{random_chars}_{str(ObjectId())}@huma.com"


def _create_organization(
    deployment_ids: list[str], db: Database, session: ClientSession, org_id: str = None
) -> str:
    org_dict = {
        Organization.ID_: ObjectId(org_id),
        Organization.NAME: "ORG to test dashboards",
        Organization.ENROLLMENT_TARGET: 3000,
        Organization.STUDY_COMPLETION_TARGET: 500,
        Organization.STATUS: Status.DEPLOYED.value,
        Organization.DEPLOYMENT_IDS: deployment_ids,
        Organization.TARGET_CONSENTED: 1050,
        Organization.DASHBOARD_ID: DashboardId.ORGANIZATION_OVERVIEW.value,
        Organization.VIEW_TYPE: ViewType.DCT.value,
    }
    id_ = (
        db.get_collection(MongoOrganizationRepository.ORGANIZATION_COLLECTION)
        .insert_one(org_dict, session=session)
        .inserted_id
    )
    logger.warning(f"Organization with ID {id_} has been created")
    return str(id_)


def _generate_users_data(
    deployment_id: str, econsent_id: ObjectId, data_config: dict
) -> Tuple[list[dict], list[dict], list[dict]]:
    users_to_create = []
    auth_users_to_create = []
    econsent_logs_to_create = []

    with open(data_config[USER_DATA_PATH]) as csv_file:
        users_data = csv.DictReader(csv_file)
        for row in users_data:
            signed_up_date = datetime.datetime.strptime(row["Signed up"], "%d/%m/%Y")
            user_dict = _create_sample_user_dict(
                deployment_id,
                signed_up_date,
                row[IN_STUDY],
                row[ID_VERIFICATION],
                row[CONSENTED],
            )
            users_to_create.append(user_dict)

            user_id = user_dict[User.ID_]
            user_email = user_dict[User.EMAIL]

            auth_user_dict = _create_auth_user_dict(user_id, signed_up_date, user_email)
            auth_users_to_create.append(auth_user_dict)

            econsent_date = row["Consented event date"]
            if econsent_id and econsent_date and row["Consented"] == "Consented":
                econsent_date = datetime.datetime.strptime(econsent_date, "%d/%m/%Y")
                log_data = _create_econsent_log_dict(
                    econsent_id, econsent_date, user_id
                )
                econsent_logs_to_create.append(log_data)

    return users_to_create, auth_users_to_create, econsent_logs_to_create


if __name__ == "__main__":
    url = "mongodb://root:password123@localhost:27027"
    mongo_client = MongoClient(url)
    database = mongo_client.get_database(db_name)
    upload_test_gadgets_data(database, mongo_client)
