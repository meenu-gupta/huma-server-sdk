import contextlib
from datetime import datetime
from typing import Set, Optional

from bson import ObjectId
from pymongo.client_session import ClientSession
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from extensions.deployment.exceptions import (
    ConsentDoesNotExist,
    ConsentSignedError,
    DeploymentDoesNotExist,
)
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.consent_repository import ConsentRepository
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values, id_as_obj_id
from sdk.phoenix.config.server_config import PhoenixServerConfig


class MongoConsentRepository(ConsentRepository):
    """Repository to work with deployment collection."""

    DEPLOYMENT_COLLECTION = "deployment"
    CONSENT_LOG_COLLECTION = "consentlog"

    session: Optional[ClientSession] = None

    @autoparams()
    def __init__(self, database: Database, config: PhoenixServerConfig):
        self._config = config
        self._db = database

    @id_as_obj_id
    def retrieve_log_count(self, consent_id: str, revision: int, user_id: str) -> bool:
        filter_options = {
            ConsentLog.CONSENT_ID: consent_id,
            ConsentLog.USER_ID: user_id,
            ConsentLog.REVISION: revision,
        }
        return self._db[self.CONSENT_LOG_COLLECTION].count_documents(filter_options)

    @id_as_obj_id
    def create_consent_log(self, deployment_id: str, consent_log: ConsentLog) -> str:
        deployment = self._db[self.DEPLOYMENT_COLLECTION].find_one(
            {
                Deployment.ID_: deployment_id,
                f"{Deployment.CONSENT}.{Consent.ID}": ObjectId(consent_log.consentId),
            }
        )
        if not deployment:
            raise ObjectDoesNotExist
        consent = deployment.get(Deployment.CONSENT)
        if consent:
            consent_log.revision = consent["revision"]
            consent_log.createDateTime = datetime.utcnow()
            consent_user_dict = consent_log.to_dict(
                ignored_fields=(ConsentLog.CREATE_DATE_TIME,)
            )
            try:
                inserted_id = str(
                    self._db[self.CONSENT_LOG_COLLECTION]
                    .insert_one(
                        remove_none_values(consent_user_dict), session=self.session
                    )
                    .inserted_id
                )
                return inserted_id
            except DuplicateKeyError:
                raise ConsentSignedError(
                    "This consent was already signed by this user."
                )
        else:
            raise ConsentDoesNotExist

    @id_as_obj_id
    def retrieve_consented_users(self, consent_id: ObjectId = None) -> Set[str]:
        aggregate_options = [
            {"$match": {ConsentLog.CONSENT_ID: consent_id}},
            {"$group": {"_id": "$userId"}},
        ]
        result = self._db[self.CONSENT_LOG_COLLECTION].aggregate(aggregate_options)
        return {str(item["_id"]) for item in result}

    @id_as_obj_id
    def create_consent(self, deployment_id: str, consent: Consent) -> str:
        deployment = self._db.deployment.find_one(
            filter={Deployment.ID_: deployment_id},
            projection={Deployment.CONSENT: 1},
        )
        if not deployment:
            raise DeploymentDoesNotExist

        consent_id = None
        if old_consent := deployment.get(Deployment.CONSENT):
            consent.bump_revision(old_consent.get(Consent.REVISION))
            consent_id = old_consent.get(Consent.ID)

        consent.set_field_value(Consent.ID, ObjectId(consent_id))
        consent.createDateTime = datetime.utcnow()

        consent_dict = consent.to_dict(False, [Consent.CREATE_DATE_TIME])
        consent_dict[Consent.ID] = ObjectId(consent.id)

        self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {Deployment.ID_: deployment_id},
            {"$set": {Deployment.CONSENT: remove_none_values(consent_dict)}},
            session=self.session,
        )

        return consent.id
