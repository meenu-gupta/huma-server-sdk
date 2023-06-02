from collections import defaultdict
from datetime import datetime, date
from typing import Any, Optional, Set

from bson import ObjectId
from pymongo.client_session import ClientSession
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from extensions.deployment.exceptions import (
    EConsentDoesNotExist,
    EConsentSignedError,
    DeploymentDoesNotExist,
)
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.models.status import EnableStatus
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.utils import build_date
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import (
    remove_none_values,
    id_as_obj_id,
    utc_str_field_to_val,
)
from sdk.phoenix.config.server_config import PhoenixServerConfig


class MongoEConsentRepository(EConsentRepository):
    """Repository to work with deployment collection."""

    DEPLOYMENT_COLLECTION = "deployment"
    ECONSENT_LOG_COLLECTION = "econsentlog"
    session: Optional[ClientSession] = None

    @autoparams()
    def __init__(
        self,
        database: Database,
        config: PhoenixServerConfig,
        repo: DeploymentRepository,
    ):
        self._config = config
        self._db = database
        self._deployment_repository = repo

    @id_as_obj_id
    def retrieve_log_count(self, consent_id: str, revision: int, user_id: str) -> bool:
        filter_options = {
            EConsentLog.ECONSENT_ID: consent_id,
            EConsentLog.USER_ID: user_id,
            EConsentLog.REVISION: revision,
        }
        return self._db[self.ECONSENT_LOG_COLLECTION].count_documents(filter_options)

    @id_as_obj_id
    def retrieve_latest_econsent(self, deployment_id: ObjectId) -> Optional[EConsent]:
        deployment: Deployment = self._deployment_repository.retrieve_deployment(
            deployment_id=str(deployment_id)
        )
        if (
            not deployment.econsent
            or deployment.econsent.enabled != EnableStatus.ENABLED
        ):
            return None
        return deployment.econsent

    @id_as_obj_id
    def create_econsent_log(
        self, deployment_id: ObjectId, econsent_log: EConsentLog
    ) -> str:
        deployment = self._db[self.DEPLOYMENT_COLLECTION].find_one(
            {
                Deployment.ID_: deployment_id,
                f"{Deployment.ECONSENT}.{EConsent.ID}": ObjectId(
                    econsent_log.econsentId
                ),
            }
        )
        if not deployment:
            raise ObjectDoesNotExist
        econsent = deployment["econsent"]
        if econsent:
            econsent_log.revision = econsent["revision"]
            econsent_log.createDateTime = datetime.utcnow()
            econsent_user_dict = econsent_log.to_dict(
                ignored_fields=(EConsentLog.CREATE_DATE_TIME,)
            )
            try:
                inserted_id = str(
                    self._db[self.ECONSENT_LOG_COLLECTION]
                    .insert_one(
                        remove_none_values(econsent_user_dict), session=self.session
                    )
                    .inserted_id
                )
                return inserted_id
            except DuplicateKeyError:
                raise EConsentSignedError(
                    "This EConsent was already signed by this user."
                )
        else:
            raise EConsentDoesNotExist

    def _signed_econsent_query(self, econsent_id: ObjectId):
        return {
            "$match": {
                EConsentLog.ECONSENT_ID: econsent_id,
                "$or": [
                    {EConsentLog.CONSENT_OPTION: None},
                    {
                        EConsentLog.CONSENT_OPTION: EConsentLog.EConsentOption.UNDERSTAND_AND_ACCEPT
                    },
                ],
            }
        }

    @id_as_obj_id
    def retrieve_consented_users(
        self,
        econsent_id: ObjectId,
        from_date_time: datetime = None,
        to_date_time: datetime = None,
    ) -> Set[str]:
        # date_range = {}
        if from_date_time:
            pass  # todo add date range query
            # date_range[]
        aggregate_options = [
            self._signed_econsent_query(econsent_id),
            {"$group": {"_id": "$userId"}},
        ]
        result = self._db[self.ECONSENT_LOG_COLLECTION].aggregate(aggregate_options)
        return {str(item["_id"]) for item in result}

    @id_as_obj_id
    def retrieve_consented_users_count(self, econsent_id: ObjectId) -> dict[str, int]:
        aggregate_options = [
            self._signed_econsent_query(econsent_id),
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$createDateTime"},
                        "month": {"$month": "$createDateTime"},
                    },
                    "usersCount": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        result = self._db[self.ECONSENT_LOG_COLLECTION].aggregate(aggregate_options)
        # todo check query for users duplicating multiple econsent sign

        return {build_date(item): item["usersCount"] for item in result}

    @id_as_obj_id
    def create_econsent(
        self, deployment_id: ObjectId, econsent: EConsent, session: ClientSession = None
    ) -> str:
        deployment = self._db.deployment.find_one(
            filter={Deployment.ID_: deployment_id},
            projection={Deployment.ECONSENT: 1},
        )
        if not deployment:
            raise DeploymentDoesNotExist

        econsent_id = None
        if old_econsent := deployment.get(Deployment.ECONSENT):
            econsent.bump_revision(old_econsent.get(EConsent.REVISION))
            econsent_id = old_econsent.get(EConsent.ID)

        econsent.set_field_value(EConsent.ID, ObjectId(econsent_id))
        econsent.createDateTime = datetime.utcnow()

        econsent_dict = econsent.to_dict(False, [EConsent.CREATE_DATE_TIME])
        econsent_dict[EConsent.ID] = ObjectId(econsent.id)

        self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {Deployment.ID_: deployment_id},
            {"$set": {Deployment.ECONSENT: remove_none_values(econsent_dict)}},
            session=self.session,
        )

        return econsent.id

    @id_as_obj_id
    def withdraw_econsent(self, log_id: ObjectId) -> dict[str, Any]:

        econsent_log = self._db[self.ECONSENT_LOG_COLLECTION].update_one(
            {EConsentLog.ID_: log_id},
            {"$set": {EConsentLog.END_DATE_TIME: datetime.utcnow()}},
        )
        return econsent_log

    @id_as_obj_id
    def retrieve_econsent_pdfs(self, econsent_id: ObjectId, user_id: ObjectId) -> dict:
        query = {
            EConsentLog.ECONSENT_ID: econsent_id,
            "$or": [
                {EConsentLog.END_DATE_TIME: None},
                {EConsentLog.END_DATE_TIME: {"$gt": datetime.utcnow().isoformat()}},
            ],
        }
        if user_id:
            query[EConsentLog.USER_ID] = user_id
            return self._retrieve_econsent_logs_for_one_user(query)
        else:
            return self._retrieve_econsent_logs_for_all_users(query)

    @id_as_obj_id
    def retrieve_signed_econsent_logs(
        self, econsent_id: ObjectId, user_id: ObjectId
    ) -> dict:
        query = {
            EConsentLog.ECONSENT_ID: econsent_id,
            "$and": [
                {
                    "$or": [
                        {EConsentLog.CONSENT_OPTION: None},
                        {
                            EConsentLog.CONSENT_OPTION: EConsentLog.EConsentOption.UNDERSTAND_AND_ACCEPT
                        },
                    ]
                },
                {
                    "$or": [
                        {EConsentLog.END_DATE_TIME: None},
                        {
                            EConsentLog.END_DATE_TIME: {
                                "$gt": datetime.utcnow().isoformat()
                            }
                        },
                    ]
                },
            ],
        }

        if user_id:
            query[EConsentLog.USER_ID] = user_id
            return self._retrieve_econsent_logs_for_one_user(query)
        else:
            return self._retrieve_econsent_logs_for_all_users(query)

    @id_as_obj_id
    def update_user_econsent_pdf_location(self, pdf_location: str, inserted_id: str):
        self._db[self.ECONSENT_LOG_COLLECTION].update_one(
            {EConsentLog.ID_: inserted_id},
            {"$set": {EConsentLog.PDF_LOCATION: pdf_location}},
            session=self.session,
        )

    @id_as_obj_id
    def retrieve_signed_econsent_log(
        self, user_id: ObjectId, log_id: ObjectId
    ) -> dict[str, Any]:
        query = {
            EConsentLog.ID_: log_id,
            EConsentLog.USER_ID: user_id,
            "$and": [
                {
                    "$or": [
                        {EConsentLog.CONSENT_OPTION: None},
                        {
                            EConsentLog.CONSENT_OPTION: EConsentLog.EConsentOption.UNDERSTAND_AND_ACCEPT
                        },
                    ]
                },
                {
                    "$or": [
                        {EConsentLog.END_DATE_TIME: None},
                        {
                            EConsentLog.END_DATE_TIME: {
                                "$gt": datetime.utcnow().isoformat()
                            }
                        },
                    ]
                },
            ],
        }
        econsent_log = self._db[self.ECONSENT_LOG_COLLECTION].find_one(query)
        if not econsent_log:
            raise ObjectDoesNotExist("Signed EConsentLog Does not exist")
        return econsent_log

    @staticmethod
    def _prepare_econsent_pdf_response(econsent_log: dict[str, Any]) -> dict[str, Any]:
        econsent_log[EConsentLog.USER_ID] = str(econsent_log[EConsentLog.USER_ID])
        econsent_log[EConsentLog.ECONSENT_ID] = str(
            econsent_log[EConsentLog.ECONSENT_ID]
        )
        econsent_log[EConsentLog.CREATE_DATE_TIME] = utc_str_field_to_val(
            econsent_log[EConsentLog.CREATE_DATE_TIME]
        )
        econsent_log[EConsentLog.ID] = str(econsent_log.pop(EConsentLog.ID_))
        return econsent_log

    def _retrieve_econsent_logs_for_one_user(self, query: dict) -> dict:
        res = self._db[self.ECONSENT_LOG_COLLECTION].find(query)

        return {
            str(log[EConsentLog.REVISION]): self._prepare_econsent_pdf_response(log)
            for log in res
        }

    def _retrieve_econsent_logs_for_all_users(self, query: dict) -> dict:
        res = self._db[self.ECONSENT_LOG_COLLECTION].find(query)

        result = defaultdict(dict)
        for each_econsent_log in res:
            result[str(each_econsent_log[EConsentLog.USER_ID])][
                str(each_econsent_log[EConsentLog.REVISION])
            ] = self._prepare_econsent_pdf_response(each_econsent_log)
        return result
