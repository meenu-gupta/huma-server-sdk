from datetime import datetime
from typing import Optional

from bson import ObjectId
from pymongo.database import Database

from extensions.identity_verification.models.identity_verification_log import (
    VerificationLog,
    Document,
)
from extensions.identity_verification.repository.verification_log_repository import (
    VerificationLogRepository,
)
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values, id_as_obj_id
from sdk.phoenix.config.server_config import PhoenixServerConfig


class MongoVerificationLogRepository(VerificationLogRepository):
    """ Repository to work with verification log collection. """

    VERIFICATION_LOG_COLLECTION = "verificationlog"
    IGNORED_FIELDS = (
        VerificationLog.CREATE_DATE_TIME,
        VerificationLog.UPDATE_DATE_TIME,
    )

    @autoparams()
    def __init__(
        self,
        database: Database,
        config: PhoenixServerConfig,
    ):
        self._config = config
        self._db = database

    @id_as_obj_id
    def retrieve_verification_log(
        self, user_id, deployment_id
    ) -> Optional[VerificationLog]:
        log = self._db[self.VERIFICATION_LOG_COLLECTION].find_one(
            {
                VerificationLog.USER_ID: user_id,
                VerificationLog.DEPLOYMENT_ID: deployment_id,
            }
        )
        if not log:
            return None

        log[VerificationLog.ID] = str(log[VerificationLog.ID_])
        return VerificationLog.from_dict(log)

    @staticmethod
    def _prepare_set_query_for_update(current_log, new_log) -> dict:
        documents = []
        if current_log.get(VerificationLog.DOCUMENTS):
            documents = [
                {Document.ID: doc[Document.ID], Document.IS_ACTIVE: False}
                for doc in current_log[VerificationLog.DOCUMENTS]
            ]
        if new_log.get(VerificationLog.DOCUMENTS):
            documents = new_log[VerificationLog.DOCUMENTS] + documents

        return {
            "$set": {
                VerificationLog.DOCUMENTS: documents,
                VerificationLog.UPDATE_DATE_TIME: datetime.utcnow(),
            }
        }

    def create_or_update_verification_log(
        self, verification_log: VerificationLog
    ) -> str:
        match_query = {
            VerificationLog.USER_ID: ObjectId(verification_log.userId),
            VerificationLog.DEPLOYMENT_ID: ObjectId(verification_log.deploymentId),
        }
        now = datetime.utcnow()
        verification_log.createDateTime = verification_log.updateDateTime = now
        verification_log_dict = verification_log.to_dict(
            ignored_fields=self.IGNORED_FIELDS
        )

        result = self.retrieve_verification_log(
            user_id=verification_log.userId,
            deployment_id=verification_log.deploymentId,
        )
        if result:
            set_query = self._prepare_set_query_for_update(
                result.to_dict(include_none=False), verification_log_dict
            )
        else:
            set_query = {"$set": remove_none_values(verification_log_dict)}

        updated_one = self._db[self.VERIFICATION_LOG_COLLECTION].update_one(
            match_query, set_query, upsert=True
        )
        return str(updated_one.upserted_id or result.id)
