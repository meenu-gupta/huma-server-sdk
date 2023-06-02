from datetime import date, timedelta, datetime
from typing import Optional

from bson import ObjectId
from mongoengine import NotUniqueError

from extensions.authorization.models.user import User, RoleAssignment
from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.export_deployment.exceptions import DuplicateProfileName
from extensions.export_deployment.models.export_deployment_models import (
    ExportProfile,
    ExportProcess,
)
from extensions.export_deployment.models.mongo_export_deployment_models import (
    MongoExportProfile,
    MongoExportProcess,
)
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
    ExportTypes,
)
from extensions.export_deployment.utils import SourceDatabase
from extensions.module_result.models.primitives import Primitive
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values, id_as_obj_id


class MongoExportDeploymentRepository(ExportDeploymentRepository):
    USER_COLLECTION = "user"
    CONSENT_LOG_COLLECTION = "consentlog"
    ECONSENT_LOG_COLLECTION = "econsentlog"

    @autoparams()
    def __init__(self, db: SourceDatabase):
        self.db = db

    def retrieve_users(
        self, deployment_id: str = None, user_ids: list[str] = None
    ) -> list[User]:
        query = {}
        if deployment_id:
            query[
                f"{User.ROLES}.{RoleAssignment.RESOURCE}"
            ] = f"deployment/{deployment_id}"
        if user_ids:
            query[User.ID_] = {"$in": [ObjectId(uid) for uid in user_ids]}
        res = self.db[self.USER_COLLECTION].find(remove_none_values(query))
        users = []
        for user_data in res:
            user_data[User.ID] = str(user_data.pop(User.ID_))
            users.append(User.from_dict(user_data, use_validator_field=False))
        return users

    @id_as_obj_id
    def retrieve_consent_logs(
        self,
        consent_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_ids: Optional[list] = None,
        use_creation_time: Optional[bool] = None,
    ) -> list[ConsentLog]:
        date_range_query = self._get_query_date_range(
            start_date, end_date, False, ConsentLog, use_creation_time
        )
        if user_ids:
            user_ids = [ObjectId(user_id) for user_id in user_ids]
        user_query = remove_none_values({"$in": user_ids})

        query = remove_none_values(
            {
                ConsentLog.CONSENT_ID: consent_id,
                ConsentLog.USER_ID: user_query if user_query else None,
                **date_range_query,
            }
        )

        result = self.db[self.CONSENT_LOG_COLLECTION].find(query)
        log_objects = []
        for log in result:
            log[ConsentLog.ID] = str(log.pop(ConsentLog.ID_))
            log_objects.append(ConsentLog.from_dict(log, use_validator_field=False))
        return log_objects

    @id_as_obj_id
    def retrieve_econsent_logs(self, econsent_id: str) -> list[EConsentLog]:
        query = {EConsentLog.ECONSENT_ID: econsent_id}
        result = self.db[self.ECONSENT_LOG_COLLECTION].find(query)
        log_objects = []
        for log in result:
            log[EConsentLog.ID] = str(log.pop(EConsentLog.ID_))
            log_objects.append(EConsentLog.from_dict(log, use_validator_field=False))
        return log_objects

    def retrieve_primitives(
        self,
        primitive_class: Primitive,
        module_id: str,
        deployment_id: str,
        start_date: date,
        end_date: date,
        partly_date_range: bool = False,
        user_ids: Optional[list] = None,
        use_creation_time: Optional[bool] = None,
    ) -> list[Primitive]:
        deployment_obj_id = ObjectId(deployment_id)
        if user_ids:
            user_ids = [ObjectId(user_id) for user_id in user_ids]
        user_query = remove_none_values({"$in": user_ids})

        date_range_query = MongoExportDeploymentRepository._get_query_date_range(
            start_date, end_date, partly_date_range, primitive_class, use_creation_time
        )

        query = {
            Primitive.DEPLOYMENT_ID: deployment_obj_id,
            Primitive.USER_ID: user_query if user_query else None,
            Primitive.MODULE_ID: module_id,
            **date_range_query,
        }
        primitive_name = primitive_class.__name__
        res = self.db[primitive_name.lower()].find(remove_none_values(query))
        primitives = []
        for primitive in res:
            primitive[Primitive.ID] = str(primitive.pop(Primitive.ID_))
            primitive_obj = primitive_class.from_dict(
                primitive, use_validator_field=False
            )
            primitives.append(primitive_obj)
        return primitives

    @staticmethod
    def _get_query_date_range(
        start_date,
        end_date,
        partly_range,
        primitive_class,
        use_creation_time: bool = None,
    ):
        # adding 1 day to end date, to include the end date itself, as cannot query by date object
        if end_date:
            end_date += timedelta(days=1)

        if use_creation_time:
            start_date_field = Primitive.CREATE_DATE_TIME
        else:
            start_date_field = getattr(
                primitive_class, "START_DATE_TIME", Primitive.CREATE_DATE_TIME
            )

        if partly_range:
            date_range_query = MongoExportDeploymentRepository._partly_date_range_query(
                start_date, end_date, start_date_field
            )
        else:
            date_range_query = MongoExportDeploymentRepository._date_range_query(
                start_date, end_date, start_date_field
            )

        return date_range_query if (start_date or end_date) else {}

    @staticmethod
    def _date_range_query(start_date, end_date, start_date_field):
        date_range = remove_none_values({"$gte": start_date, "$lt": end_date})
        query = {start_date_field: date_range if date_range else None}
        return query

    @staticmethod
    def _partly_date_range_query(start_date, end_date, start_date_field):
        start = remove_none_values({"$gte": start_date})
        end = remove_none_values({"$lt": end_date})
        query = remove_none_values(
            {
                "$or": [
                    {start_date_field: start},
                    {Primitive.END_DATE_TIME: end},
                ]
            }
        )
        return query

    def retrieve_export_profiles(
        self,
        name_contains: str,
        deployment_id: str = None,
        organization_id: str = None,
    ) -> list[ExportProfile]:
        query = {
            ExportProfile.DEPLOYMENT_ID: deployment_id,
            ExportProfile.ORGANIZATION_ID: organization_id,
            f"{ExportProfile.NAME}__icontains": name_contains,
        }
        export_profiles = MongoExportProfile.objects(**remove_none_values(query))
        profiles = [
            ExportProfile.from_dict(profile.to_dict()) for profile in export_profiles
        ]
        return profiles

    def create_export_profile(self, export_profile: ExportProfile) -> str:
        try:
            export_profile = MongoExportProfile(
                **export_profile.to_dict(include_none=False)
            ).save()
        except NotUniqueError:
            raise DuplicateProfileName
        return str(export_profile.id)

    def update_export_profile(self, export_profile: ExportProfile) -> str:
        query = remove_none_values(
            {
                ExportProfile.DEPLOYMENT_ID: export_profile.deploymentId,
                ExportProfile.ORGANIZATION_ID: export_profile.organizationId,
                ExportProfile.ID: export_profile.id,
            }
        )
        old_profile = MongoExportProfile.objects(**query).first()
        if not old_profile:
            raise ObjectDoesNotExist
        export_profile.updateDateTime = datetime.utcnow()
        data = export_profile.to_dict(include_none=False)
        try:
            old_profile.update(**data)
        except NotUniqueError:
            raise DuplicateProfileName
        return str(old_profile.id)

    def delete_export_profile(self, export_profile_id: str):
        result = MongoExportProfile.objects(id=export_profile_id).delete()
        if not result:
            raise ObjectDoesNotExist(
                f"Export profile {export_profile_id} does not exist"
            )

    def retrieve_export_profile(
        self,
        deployment_id: str = None,
        organization_id: str = None,
        profile_id: str = None,
        profile_name: str = None,
        default: bool = None,
    ) -> ExportProfile:
        query = remove_none_values(
            {
                ExportProfile.ID: profile_id,
                ExportProfile.DEPLOYMENT_ID: deployment_id,
                ExportProfile.ORGANIZATION_ID: organization_id,
                ExportProfile.NAME: profile_name,
                ExportProfile.DEFAULT: default,
            }
        )
        if len(query) == 1 and ExportProfile.DEFAULT in query:
            raise ObjectDoesNotExist

        profile = MongoExportProfile.objects(**query).first()

        if not profile:
            raise ObjectDoesNotExist(f"Export profile {profile_id} does not exist")
        return ExportProfile.from_dict(profile.to_dict())

    def create_export_process(self, export_process: ExportProcess) -> str:
        export_process = MongoExportProcess(
            **export_process.to_dict(include_none=False)
        ).save()
        return str(export_process.id)

    def update_export_process(
        self, export_process_id: str, export_process: ExportProcess
    ) -> str:
        old_export_process = MongoExportProcess.objects(id=export_process_id).first()
        if not old_export_process:
            raise ObjectDoesNotExist
        export_process.updateDateTime = datetime.utcnow()
        data = export_process.to_dict(include_none=False)
        old_export_process.update(**data)
        return str(old_export_process.id)

    def retrieve_export_processes(
        self,
        deployment_id: str = None,
        user_id: str = None,
        export_type: ExportTypes = None,
        status: ExportProcess.ExportStatus = None,
        till_date: datetime = None,
    ) -> list[ExportProcess]:
        export_type = export_type and [e.value for e in export_type]
        query = remove_none_values(
            {
                ExportProcess.DEPLOYMENT_ID: deployment_id,
                ExportProcess.REQUESTER_ID: user_id,
                f"{ExportProcess.EXPORT_TYPE}__in": export_type or None,
                ExportProcess.STATUS: status and status.value,
                f"{ExportProcess.CREATE_DATE_TIME}__lt": till_date,
            }
        )
        export_processes = MongoExportProcess.objects(**query)
        return [
            ExportProcess.from_dict(process.to_dict()) for process in export_processes
        ]

    def retrieve_unseen_export_process_count(self, user_id: str) -> int:
        query = {ExportProcess.REQUESTER_ID: user_id, ExportProcess.SEEN: False}
        return MongoExportProcess.objects(**query).count()

    def retrieve_export_process(self, export_process_id: str) -> ExportProcess:
        export_process = MongoExportProcess.objects(id=export_process_id).first()
        if not export_process:
            raise ObjectDoesNotExist(
                f"Export process {export_process_id} does not exist"
            )
        return ExportProcess.from_dict(export_process.to_dict())

    def check_export_process_already_running_for_user(self, requester_id: str) -> bool:
        export_process = MongoExportProcess.objects(
            requesterId=requester_id,
            status__in=[
                ExportProcess.ExportStatus.CREATED.value,
                ExportProcess.ExportStatus.PROCESSING.value,
            ],
        ).first()
        return bool(export_process)

    def delete_export_process(self, export_process_id: str):
        deleted = MongoExportProcess.objects(id=export_process_id).delete()
        if not deleted:
            raise ObjectDoesNotExist

    @id_as_obj_id
    def mark_export_processes_seen(
        self, export_process_ids: list[str], requester_id: ObjectId
    ):
        process_ids = [ObjectId(i) for i in export_process_ids]
        processes = MongoExportProcess.objects(
            id__in=process_ids, requesterId=requester_id
        )
        return processes.update(seen=True, updateDateTime=datetime.utcnow())
